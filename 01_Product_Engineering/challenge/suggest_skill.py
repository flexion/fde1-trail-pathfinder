"""Way 2, the skill (TC5): the same capability as find_skills, the policy in SKILL.md.

Session 10's call_with_skill, on the skills wiki:

1. PLAN: one model call, a schema'd `plan_searches(queries)` it must call, that names the
   wiki searches to run (at most MAX_SEARCHES). Missing or malformed arguments fall back to
   searching her whole text, recorded on the meter, never raised.
2. EXECUTE: `skills/suggest-competencies/run.py` once per query, as a subprocess. Its stderr
   `capability_call` lines are the only count of the work: no in-process counter sees it.
   A failed run becomes a `(tool error: ...)` string in the results, never an exception.
3. ANSWER: one model call with the SKILL.md body as the system prompt and the results in the
   user message, parsed like find_skills' answer, so from_text_model uses either.

SKILL.md is read on every call, so an edit to the policy takes effect on the next request.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from schema import CompetencySuggestion
from suggest import CapabilityCounter, Meter, chip_prompt, parse_answer

SKILL_DIR = Path(__file__).resolve().parent / "skills" / "suggest-competencies"
MAX_SEARCHES = 4
RUN_TIMEOUT = 60

PLAN_SCHEMA = [{"type": "function", "function": {
    "name": "plan_searches",
    "description": ("Name the skills-wiki searches to run: one per distinct task, tool or trail feature "
                    f"she names, in her words. At most {MAX_SEARCHES}."),
    "parameters": {"type": "object", "required": ["queries"], "properties": {"queries": {
        "type": "array", "items": {"type": "string"}, "maxItems": MAX_SEARCHES,
        "description": "Search queries, her words."}}},
}}]


def read_skill() -> tuple[dict, str]:
    """(frontmatter, body) of SKILL.md. The frontmatter is `key: value` lines, indented lines continuing."""
    _, front, body = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8").split("---", 2)
    meta: dict[str, str] = {}
    key = None
    for line in front.strip().splitlines():
        if line.startswith((" ", "\t")) and key:
            meta[key] += " " + line.strip()
        elif ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            meta[key] = value.strip()
    return meta, body.strip()


def run_skill(query: str, k: int = 4) -> tuple[str, int]:
    """(result text, capability calls the far side reported). Failures come back as text."""
    try:
        done = subprocess.run([sys.executable, str(SKILL_DIR / "run.py"), query, str(k)],
                              capture_output=True, text=True, timeout=RUN_TIMEOUT)
    except subprocess.TimeoutExpired:
        return f"(tool error: run.py timed out after {RUN_TIMEOUT}s)", 0
    calls = sum(line.strip().startswith("capability_call search_chunks") for line in done.stderr.splitlines())
    if done.returncode != 0:
        return f"(tool error: run.py exited {done.returncode}: {done.stderr.strip()[-300:]})", calls
    try:
        return str(json.loads(done.stdout)["result"]), calls
    except (ValueError, KeyError, TypeError) as exc:
        return f"(tool error: run.py printed no result JSON: {type(exc).__name__}: {exc})", calls


def plan(user: str, meter: Meter | None) -> list[str]:
    from litellm import completion

    from llm import _call_kwargs

    meta, _ = read_skill()
    response = completion(**_call_kwargs([{"role": "system", "content": meta.get("description", "")},
                                          {"role": "user", "content": user}],
                                         tools=PLAN_SCHEMA, tool_choice="required", timeout=60,
                                         # litellm refuses tool_choice for this gateway model name; the gateway takes it
                                         allowed_openai_params=["tool_choice"]))
    calls = response.choices[0].message.tool_calls or []
    if meter is not None:
        meter.track(response)
        meter.tool_calls_emitted += len(calls)
        meter.first_turn_tool_calls = len(calls)
    try:
        queries = [str(q).strip() for q in json.loads(calls[0].function.arguments)["queries"] if str(q).strip()]
        if not queries:
            raise ValueError("no queries")
        return queries[:MAX_SEARCHES]
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        if meter is not None:
            meter.notes.append(f"plan fell back to her whole text ({type(exc).__name__}: {exc})")
        return []


def find_skills_skill(text: str, chip_skills: list[CompetencySuggestion] = (), meter: Meter | None = None,
                      counter: CapabilityCounter | None = None, k: int = 4) -> dict:
    """Plan, run the skill per query, answer with the skill's policy. Same return shape as find_skills."""
    from litellm import completion

    from llm import _call_kwargs

    user = chip_prompt(text, chip_skills)
    queries = plan(user, meter) or [text]
    sections = []
    for query in queries:   # one at a time: each run.py rewrites the shared EMBED_CACHE file on a miss
        result, calls = run_skill(query, k)
        if counter is not None:
            counter.calls += calls
            counter.bytes.append(len(result.encode()))
        sections.append(f"### search: {query}\n{result}")
    _, body = read_skill()
    response = completion(**_call_kwargs([{"role": "system", "content": body},
                                          {"role": "user", "content": f"{user}\n\nWiki search results:\n\n"
                                                                      + "\n\n".join(sections)}],
                                         timeout=60))
    if meter is not None:
        meter.track(response)
    return parse_answer(response.choices[0].message.content)
