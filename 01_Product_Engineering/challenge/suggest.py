"""AI-1: what she has done, in her words, plus any backgrounds she picked -> competency suggestions.

Two inputs, two paths, merged:

- A background chip is a lookup: `framework.json` `backgrounds[].suggestions`, all Entry,
  no model. A chip never pre-checks a skill (TC5, fix #3): every chip skill comes back
  check, whatever the prototype's score was. Only her own words pre-check.
- Her text goes to the step 1 retriever chosen in TC3 (`use_case/decisions.md`): dense
  Agentic RAG. The model calls `search_chunks` over the trailskills.org skills wiki,
  ranked by embeddings, and names the skills her words describe, each with her exact
  words. Measured in `use_case/evals/ai1_find_skill_agent.py`.

Levels: every suggestion is Entry. Raising one needs her words to match a rubric line
(`level_basis`), which is step 2, the Week 4 judge; until then nothing is raised.

Code checks what the model says: an id not in the framework is dropped, a quote not in
her text is dropped with its suggestion, rejected ids never come back. Her words win
over a chip on the same skill. A chip skill her words point away from (the model names it,
with her words, in the same call) says so in its reason: still listed, not pre-checked. At
most 12, dropping check then possible first.

When chips are picked and her words support no skill (no text, or text that names no task),
the chip skills still come back and `follow_up_prompt` asks what the work involved.

How the model reaches the wiki is SUGGEST_WAY (TC5): "tool" (default) is the loop below, the
crediting policy in SYSTEM; "skill" is suggest_skill.py, the same policy in
skills/suggest-competencies/SKILL.md, where a product manager can change it without touching code.

If the wiki is missing or the model or embeddings fail, the text path falls back to the
prototype's keyword rules (`produced_by: "rules"`), so she still gets an answer.

The wiki is American Trails' content and is not in git or the image: WIKI_DIR points at
it (default `use_case/data/wiki`; in Docker, mount it). EMBED_CACHE is an optional file
of cached embeddings, the same one the eval script writes.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from functools import cache
from pathlib import Path

from schema import Category, CompetencySuggestion, CompetencySuggestions, Confidence, ExperienceRequest, SkillLevel

log = logging.getLogger(__name__)

HERE = Path(__file__).resolve().parent
FRAMEWORK = HERE / "data" / "framework.json"
# In the repo, use_case/data two levels up; in the container WIKI_DIR and EMBED_CACHE are set.
REPO_DATA = HERE.parents[1] / "use_case" / "data" if len(HERE.parents) > 1 else HERE / "data"
WIKI_DIR = Path(os.getenv("WIKI_DIR") or REPO_DATA / "wiki")
EMBED_CACHE = Path(os.getenv("EMBED_CACHE") or REPO_DATA / "embeddings_cache.json")
# The gateway serves no OpenAI embedding model; Titan v2 takes one text per request.
EMBED_MODEL = os.getenv("EMBED_MODEL") or "openai/bedrock/amazon.titan-embed-text-v2:0"

MAX_SUGGESTIONS = 12
MAX_TURNS = 6
MAX_K = 8
FRAMEWORK_VERSION = "role profiles and competency map 2026-10-20; trailskills.org skill pages"
FOLLOW_UP_BACKGROUND_ONLY = "Tell us what the work involved so we can confirm which suggestions fit."

SYSTEM = (
    "You find which trail skills a person's own words support, using only the skills wiki. "
    "Use your tools to look in the wiki before answering; look again with different words "
    "when a task she names has no match yet. A page name is a skill id; a chunk id is "
    "<skill-id>#<section>.\n"
    "Name a skill only when her words describe doing that work. Do not judge levels.\n"
    "If her text names no task, tool or trail feature, decline.\n"
    "You may also be given the skills her background chips suggest. Give each one a verdict: "
    '"supported" when her words describe that work; "points_away" when her words say she did '
    "not do it, or describe what she did in that field and it is a different kind of work "
    "(a landscaping chip suggests Retaining Walls, but she writes that she only mowed and "
    "watered); \"silent\" when she just does not mention it. Silent is not points_away.\n"
    'Reply with JSON only: {"skills": [{"skill_id": "...", "quote": "her exact words"}], '
    '"chips": [{"skill_id": "...", "verdict": "supported|points_away|silent", "quote": "her words, or null"}], '
    '"declined": false, "reason": null}'
)

TOOLS = [{"type": "function", "function": {
    "name": "search_chunks",
    "description": "Search ranked skill-wiki chunks. Search again with a new query when evidence is incomplete.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                   "required": ["query"]}}}]

DECLINE_VAGUE = "Not enough to go on: no task, tool or feature is named. Ask for what the work involved."
DECLINE_NOTHING = ("Nothing here maps to a trail competency. Pick a background or describe any outdoor, "
                   "construction or crew work.")
HEDGES = ("only ", "a little", "a few", "some ", "helped", "tried", "watched", "took the", "class")


@cache
def framework() -> dict:
    return json.loads(FRAMEWORK.read_text(encoding="utf-8"))


def bucket(score: float) -> Confidence:
    return Confidence.LIKELY if score >= 0.75 else Confidence.POSSIBLE if score >= 0.55 else Confidence.CHECK


def suggestion(skill_id: str, confidence: Confidence, reason: str, quote: str | None = None) -> CompetencySuggestion:
    comp = {c["id"]: c for c in framework()["competencies"]}[skill_id]
    return CompetencySuggestion(skill_id=skill_id, category=Category(comp["category"]), skill=comp["name"],
                                level=SkillLevel.ENTRY, confidence=confidence, reason=reason, quote=quote)


# --- the wiki and its search -------------------------------------------------------------


@cache
def chunks() -> tuple[dict, ...]:
    """Each wiki page split at `##`, the skill's title and category kept on every chunk.
    Same text as the eval script builds, so the embedding cache is shared."""
    out = []
    for path in sorted(WIKI_DIR.glob("*.md")):
        if path.stem == "index":
            continue
        lines = [ln.split(" · ")[0] if ln.startswith("Category:") else ln
                 for ln in path.read_text(encoding="utf-8").splitlines()]
        header, *sections = re.split(r"(?=^## )", "\n".join(lines), flags=re.M)
        for section in sections:
            heading = section.splitlines()[0].lstrip("# ").strip().lower().replace(" ", "-")
            out.append({"id": f"{path.stem}#{heading}", "text": f"{header.strip()}\n{section.strip()}"})
    if not out:
        raise FileNotFoundError(f"no skill pages in {WIKI_DIR}")
    return tuple(out)


_embed_cache: dict[str, list[float]] = {}


def _embed_one(text: str) -> list[float]:
    import litellm

    from llm import API_BASE, EXTRA_HEADERS

    kwargs = {"model": EMBED_MODEL, "input": [text], "timeout": 60}
    if API_BASE:
        kwargs["api_base"] = API_BASE
    if EXTRA_HEADERS:
        kwargs["extra_headers"] = EXTRA_HEADERS
    return litellm.embedding(**kwargs).data[0]["embedding"]


def embed(texts: list[str]):
    """Unit-length vectors, cached in memory and, when EMBED_CACHE is readable, on disk."""
    import numpy as np

    if not _embed_cache and EMBED_CACHE.exists():
        _embed_cache.update(json.loads(EMBED_CACHE.read_text()))
    keys = [hashlib.sha256(f"{EMBED_MODEL}\n{t}".encode()).hexdigest() for t in texts]
    missing = [(k, t) for k, t in zip(keys, texts) if k not in _embed_cache]
    if missing:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for (k, _), vec in zip(missing, pool.map(lambda kt: _embed_one(kt[1]), missing)):
                _embed_cache[k] = vec
        try:
            EMBED_CACHE.write_text(json.dumps(_embed_cache))
        except OSError:
            pass   # a read-only mount: the cache stays in memory
    vecs = np.asarray([_embed_cache[k] for k in keys], dtype=np.float32)
    return vecs / np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)


@cache
def chunk_matrix():
    return embed([c["text"] for c in chunks()])


def search_chunks(query: str, k: int = 4) -> str:
    scores = chunk_matrix() @ embed([query])[0]
    order = scores.argsort()[::-1][: max(1, min(int(k), MAX_K))]
    return "\n\n---\n\n".join(f"[{chunks()[i]['id']}]\n{chunks()[i]['text'][:1000]}" for i in order)


class Meter:
    """What the loop cost: model round trips, their tokens, and the tool calls the model emitted."""

    def __init__(self):
        self.calls = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.first_turn_tool_calls: int | None = None   # len(msg.tool_calls) on turn one
        self.tool_calls_emitted = 0
        self.notes: list[str] = []

    def track(self, response):
        self.calls += 1
        usage = getattr(response, "usage", None)
        if usage:
            self.prompt_tokens += usage.prompt_tokens or 0
            self.completion_tokens += usage.completion_tokens or 0
            self.total_tokens += usage.total_tokens or 0


class CapabilityCounter:
    """What the work was: how many times search_chunks ran, and the bytes each run returned."""

    def __init__(self):
        self.calls = 0
        self.bytes: list[int] = []


TOOL_NAMES = [t["function"]["name"] for t in TOOLS]


def dispatch(call: dict, search=search_chunks, counter: CapabilityCounter | None = None) -> str:
    """One tool call from the model -> the text the model gets back.

    A wrong tool name or bad arguments is a message to the model, never an exception, and never
    a search: a loop with no name check runs search_chunks for any name the model makes up.
    A failed search still raises, so the caller falls back to the rules instead of letting the
    model guess ids it never saw.
    """
    name = call["function"]["name"]
    if name not in TOOL_NAMES:
        return f"Unknown tool: {name!r}. Available tools: {', '.join(TOOL_NAMES)}"
    try:
        args = json.loads(call["function"]["arguments"] or "{}")
        if not isinstance(args, dict):
            raise TypeError(f"expected an object like {{\"query\": \"...\"}}, got {type(args).__name__}")
        query, k = str(args["query"]), int(args.get("k", 4))
    except json.JSONDecodeError as exc:
        return f"(tool error: arguments were not a JSON object: {exc})"
    except KeyError as exc:
        return f"(tool error: missing required argument {exc}. search_chunks takes query (string) and k (integer))"
    except (TypeError, ValueError) as exc:
        return f"(tool error: {type(exc).__name__}: {exc})"
    result = search(query=query, k=k)
    if counter is not None:
        counter.calls += 1
        counter.bytes.append(len(result.encode()))
    return result


def parse_answer(content: str | None) -> dict:
    found = re.search(r"\{.*\}", content or "", re.S)
    if not found:
        raise ValueError("model reply had no JSON")
    return json.loads(found.group(0))


def chip_prompt(text: str, chip_skills: list[CompetencySuggestion] = ()) -> str:
    if not chip_skills:
        return text
    listed = "\n".join(f"- {s.skill_id}: {s.skill} ({s.category})" for s in chip_skills)
    return f"{text}\n\nSkills her background chips suggest:\n{listed}"


def find_skills(text: str, chip_skills: list[CompetencySuggestion] = (), meter: Meter | None = None,
                counter: CapabilityCounter | None = None, search=search_chunks) -> dict:
    """Way 1, the tool: Session 5's loop, the model calls search_chunks until it answers.
    Returns its parsed JSON. The chip skills ride along in the same call so it can say which her
    words contradict. `search` is the capability, an argument so a measurement can wrap it."""
    from litellm import completion

    from llm import _call_kwargs

    messages: list[dict] = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": chip_prompt(text, chip_skills)}]
    for turn in range(MAX_TURNS):
        response = completion(**_call_kwargs(messages, tools=TOOLS, timeout=60))
        msg = response.choices[0].message
        calls = msg.tool_calls or []
        if meter is not None:
            meter.track(response)
            meter.tool_calls_emitted += len(calls)
            if turn == 0:
                meter.first_turn_tool_calls = len(calls)
        if not calls:
            return parse_answer(msg.content)
        shaped = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                  for c in calls]
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": shaped})
        for call in shaped:
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": dispatch(call, search, counter)})
    raise TimeoutError(f"no answer in {MAX_TURNS} turns")


# --- the two paths -----------------------------------------------------------------------


def from_backgrounds(backgrounds: list[str]) -> list[CompetencySuggestion]:
    by_id = {b["id"]: b for b in framework()["backgrounds"]}
    out = []
    for bid in backgrounds:
        bg = by_id[bid]
        for item in bg["suggestions"]:
            out.append(suggestion(item["skill_id"], bucket(item["confidence"]),
                                  f"Common for people with {bg['label'].lower()} experience"))
    return out


def from_text_model(text: str, chip_skills: list[CompetencySuggestion] = (), way: str | None = None,
                    **measure) -> tuple[list[CompetencySuggestion], set[str]]:
    """(suggestions, chip skill ids her words contradict) from the dense agent, with every id
    and quote checked. A decline is an empty list. A contradiction counts only for a chip skill
    actually listed, with a quote of hers that is really in her text.

    `way` (default: SUGGEST_WAY, else "tool") picks how the model reaches the wiki: "tool" is
    find_skills' loop, "skill" is suggest_skill.find_skills_skill. `measure` goes to that function
    (meter, counter, and search for the tool or k for the skill)."""
    known = {c["id"] for c in framework()["competencies"]}
    way = way or os.getenv("SUGGEST_WAY") or "tool"
    if way == "skill":
        from suggest_skill import find_skills_skill

        answer = find_skills_skill(text, chip_skills, **measure)
    elif way == "tool":
        answer = find_skills(text, chip_skills, **measure)
    else:
        raise ValueError(f"SUGGEST_WAY must be 'tool' or 'skill', not {way!r}")
    listed = {s.skill_id for s in chip_skills}
    contradicted = set()
    for item in answer.get("chips") or []:
        if isinstance(item, dict) and item.get("verdict") == "points_away":
            sid, quote = str(item.get("skill_id", "")), str(item.get("quote") or "").strip().strip('"')
            if sid in listed and quote and quote.casefold() in text.casefold():
                contradicted.add(sid)
    out = []
    for item in answer.get("skills") or []:
        if not isinstance(item, dict):
            continue
        sid = str(item.get("skill_id", "")).split("#")[0]
        quote = (item.get("quote") or "").strip().strip('"')
        if sid not in known or not quote or quote.casefold() not in text.casefold():
            log.info("dropped model suggestion %r (unknown id or quote not in her text)", item)
            continue
        hedged = any(h in quote.casefold() for h in HEDGES)
        out.append(suggestion(sid, Confidence.CHECK if hedged else Confidence.LIKELY, f'You wrote "{quote}"', quote))
    return out, contradicted


def from_text_rules(text: str) -> list[CompetencySuggestion]:
    """The prototype's keyword rules: the fallback when the model or the wiki is unavailable."""
    lowered = text.casefold()
    out = []
    for rule in framework()["keyword_rules"]:
        hit = next((word for word in rule["match"] if word in lowered), None)
        if hit:
            start = lowered.index(hit)
            quote = text[start:start + len(hit)]
            out.append(suggestion(rule["skill_id"], Confidence.POSSIBLE, f'You wrote "{quote}"', quote))
    return out


def suggest(request: ExperienceRequest, *, way: str | None = None, **measure) -> CompetencySuggestions:
    known_bg = {b["id"] for b in framework()["backgrounds"]}
    backgrounds = [b for b in request.backgrounds if b in known_bg]
    text = request.text.strip()

    chip_found = from_backgrounds(backgrounds)
    text_found: list[CompetencySuggestion] = []
    contradicted: set[str] = set()
    produced_by = "rules"
    if text:
        started = time.perf_counter()
        try:
            text_found, contradicted = from_text_model(text, chip_found, way, **measure)
            produced_by = "model"
        except Exception as exc:   # wiki missing, gateway down, bad reply: the rules still answer
            log.warning("AI-1 model path failed (%s: %s); using keyword rules", type(exc).__name__, exc)
            text_found = from_text_rules(text)
        log.info("AI-1 text path %s in %.1fs", produced_by, time.perf_counter() - started)

    # Background chips suggest skills, but never pre-check them.
    chip_found = [
        s.model_copy(update={"confidence": Confidence.CHECK})
        for s in chip_found
    ]

    # A chip skill her words point away from stays on the list but is not pre-checked.
    chip_found = [s.model_copy(update={"confidence": Confidence.CHECK,
                                       "reason": f"{s.reason}, but what you wrote points to other work"})
                  if s.skill_id in contradicted else s for s in chip_found]

    # Her words win on overlap; then the chips, in the order she picked them.
    merged: dict[str, CompetencySuggestion] = {}
    for sug in text_found + chip_found:
        if sug.skill_id not in merged and sug.skill_id not in request.rejected:
            merged[sug.skill_id] = sug
    ranked = list(merged.values())
    for drop in (Confidence.CHECK, Confidence.POSSIBLE):
        while len(ranked) > MAX_SUGGESTIONS and any(s.confidence == drop for s in ranked):
            ranked.remove(next(s for s in reversed(ranked) if s.confidence == drop))
    ranked = ranked[:MAX_SUGGESTIONS]

    if not ranked:
        # Trail words with no task named is "tell me more"; anything else is "nothing maps".
        vague = bool(re.search(r"\b(trail|crew|outdoor)", text, re.I))
        return CompetencySuggestions(declined=True, reason=DECLINE_VAGUE if vague else DECLINE_NOTHING,
                                     produced_by=produced_by if text else "rules")
    return CompetencySuggestions(
        suggestions=ranked,
        sources=[f"framework:competency:{s.skill_id}" for s in ranked] + [f"framework:background:{b}" for b in backgrounds],
        framework_version=FRAMEWORK_VERSION,
        produced_by=produced_by if text_found or not backgrounds else "rules",
        follow_up_prompt=FOLLOW_UP_BACKGROUND_ONLY if not text_found else None,
    )
