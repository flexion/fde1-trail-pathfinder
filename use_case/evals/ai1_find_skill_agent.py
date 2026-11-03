"""AI-1 step 1 as Session 5's agent loop: the model searches the wiki and names the skills.

    uv run --group week3 python use_case/evals/ai1_find_skill_agent.py
    uv run --group week3 python use_case/evals/ai1_find_skill_agent.py --techniques dense --only retrieval-03

ai1_find_skill.py scores the ranked pages with no model. This one gives the model
tools over the same wiki and asks it which skills her words support, each with
the words of hers it rests on. Levels are step 2. The loop and prompt are the
same for every technique; only the tools change:

    bm25   Agentic RAG: `search_chunks`, ranked by BM25 (ai1_find_skill.py)
    dense  Agentic RAG: `search_chunks`, ranked by embeddings (ai1_find_skill.py)
    dci    Session 5's direct corpus interaction: `list_pages` (the wiki index, one
           line per skill), `grep_wiki` (regex with line provenance), `read_page`

Chunks: each page split at `##` (Definition, Entry, Full Performance, Expert),
id `<skill-id>#<section>`, with the skill name and category kept on every chunk so a level
section still says which skill it belongs to (the twins differ only by category).

Scored on retrieval.jsonl, Session 5's columns adapted to skill ids:
    found    gold skills it named / gold skills (twins count as one: either passes)
    wrong    skills it named that are not gold
    quotes   its quotes that are really in her text
    decline  a decline case passes when it declines and names nothing
    calls, evidence chars, latency, how the loop stopped

Each case runs --runs times (default 3); the table gives the mean and the range.

Needs a model in .env. Writes ai1_find_skill_agent_results.md and .jsonl (every answer and trace).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ai1_find_skill import ROOT, load_cases, load_pages, make_retriever, match, twin_groups  # noqa: E402

sys.path.insert(0, str(ROOT))
OUT_MD = ROOT / "use_case" / "evals" / "ai1_find_skill_agent_results.md"
OUT_JSONL = ROOT / "use_case" / "evals" / "ai1_find_skill_agent_results.jsonl"

MAX_TURNS = 6
MAX_K = 8

SYSTEM = (
    "You find which trail skills a person's own words support, using only the skills wiki. "
    "Use your tools to look in the wiki before answering; look again with different words "
    "when a task she names has no match yet. A page name is a skill id; a chunk id is "
    "<skill-id>#<section>.\n"
    "Name a skill only when her words describe doing that work. Do not judge levels.\n"
    "If her text names no task, tool or trail feature, decline.\n"
    'Reply with JSON only: {"skills": [{"skill_id": "...", "quote": "her exact words"}], '
    '"declined": false, "reason": null}'
)


def build_chunks(pages: dict[str, str]) -> list[dict]:
    chunks = []
    for sid, text in pages.items():
        header, *sections = re.split(r"(?=^## )", text, flags=re.M)   # header: title + category
        for section in sections:
            heading = section.splitlines()[0].lstrip("# ").strip().lower().replace(" ", "-")
            chunks.append({"id": f"{sid}#{heading}", "skill": sid, "text": f"{header.strip()}\n{section.strip()}"})
    return chunks


def make_search(chunks: list[dict], technique: str):
    texts = {c["id"]: c["text"] for c in chunks}
    retriever = make_retriever(technique, texts)

    def search_chunks(query: str, k: int = 4) -> str:
        order = [cid for cid, _ in retriever.rank(query)[: max(1, min(k, MAX_K))]]
        return "\n\n---\n\n".join(f"[{cid}]\n{texts[cid][:1000]}" for cid in order)

    return search_chunks


def make_dci(pages: dict[str, str]) -> dict:
    index = (ROOT / "use_case" / "data" / "wiki" / "index.md").read_text(encoding="utf-8")

    def list_pages() -> str:
        return index

    def grep_wiki(pattern: str) -> str:
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            rx = re.compile(re.escape(pattern), re.I)
        hits = [f"{sid}:{n}: {line}" for sid, text in pages.items()
                for n, line in enumerate(text.splitlines(), 1) if rx.search(line)]
        return "\n".join(hits[:40]) or "(no matches)"

    def read_page(page: str) -> str:
        page = page.removesuffix(".md")
        return pages.get(page, f"(unknown page: {page})")

    return {"list_pages": list_pages, "grep_wiki": grep_wiki, "read_page": read_page}


def schema(name: str, description: str, properties: dict, required: tuple = ()) -> dict:
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)}}}


SEARCH_TOOLS = [schema("search_chunks", "Search ranked skill-wiki chunks. Search again with a new query when evidence is incomplete.",
                       {"query": {"type": "string"}, "k": {"type": "integer"}}, ("query",))]


def dci_tools(pages: dict[str, str]) -> list[dict]:
    return [
        schema("list_pages", "Read the wiki index: every skill page by category, with its one-line definition.", {}),
        schema("grep_wiki", "Search exact text or a regular expression across wiki pages, with line provenance.",
               {"pattern": {"type": "string"}}, ("pattern",)),
        schema("read_page", "Read one complete skill page by its name (the skill id).",
               {"page": {"type": "string", "enum": sorted(pages)}}, ("page",)),
    ]


def run_agent(cfg, question: str, tools: list[dict], funcs: dict) -> dict:
    """Session 5's loop: call tools until the model answers, at most MAX_TURNS turns."""
    import litellm
    from helpers.llm import complete

    litellm.suppress_debug_info = True

    messages: list[dict] = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    trace: list[dict] = []
    chars = 0
    started = time.perf_counter()
    for _ in range(MAX_TURNS):
        msg = complete(cfg, messages, tools=tools, timeout=120).choices[0].message
        calls = msg.tool_calls or []
        if not calls:
            return {"answer": (msg.content or "").strip(), "trace": trace, "evidence_chars": chars,
                    "latency_s": time.perf_counter() - started, "stopped": "answer"}
        shaped = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}}
                  for c in calls]
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": shaped})
        for call in shaped:
            name, args = call["function"]["name"], {}
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
                result = str(funcs[name](**args))
            except Exception as exc:
                result = f"(tool error: {type(exc).__name__}: {exc})"
            chars += len(result)
            trace.append({"tool": name, "args": args, "chars": len(result)})
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return {"answer": "", "trace": trace, "evidence_chars": chars,
            "latency_s": time.perf_counter() - started, "stopped": "max_turns"}


def parse(answer: str) -> dict | None:
    match = re.search(r"\{.*\}", answer, re.S)
    try:
        return json.loads(match.group(0)) if match else None
    except json.JSONDecodeError:
        return None


def score(case: dict, result: dict, twins: dict[str, frozenset[str]]) -> dict:
    parsed = parse(result["answer"])
    skills = (parsed or {}).get("skills") or []
    # A chunk id (<skill-id>#<section>) names the same skill; the section is not the claim.
    named = [s["skill_id"].split("#")[0] for s in skills if isinstance(s, dict) and isinstance(s.get("skill_id"), str)]
    text = case["question"].casefold()
    found, total, missed, wrong = match(case["gold"], named, twins)
    row = {
        "id": case["id"], "kind": case["kind"],
        "parsed": parsed is not None,
        "found": f"{found}/{total}",
        "missed": missed,
        "wrong": wrong,
        "unknown_ids": sorted(set(named) - set(twins)),
        "quotes_ok": f"{sum(bool(s.get('quote')) and s['quote'].casefold() in text for s in skills)}/{len(skills)}",
        "calls": len(result["trace"]),
        "evidence_chars": result["evidence_chars"],
        "latency_s": round(result["latency_s"], 1),
        "stopped": result["stopped"],
    }
    if case["kind"] == "decline":
        row["pass"] = bool(parsed and parsed.get("declined") and not named)
    else:
        row["pass"] = not row["missed"]
    return row


def run_summary(rows: list[dict]) -> dict:
    """One run of one technique over every case."""
    answerable = [r for r in rows if r["kind"] != "decline"]
    declines = [r for r in rows if r["kind"] == "decline"]
    quotes = [r["quotes_ok"].split("/") for r in rows]
    n = len(rows)
    return {
        "all_found": sum(r["pass"] for r in answerable),
        "recall": sum(int(r["found"].split("/")[0]) for r in answerable)
        / max(1, sum(int(r["found"].split("/")[1]) for r in answerable)),
        "wrong": sum(len(r["wrong"]) for r in rows),
        "declines": sum(r["pass"] for r in declines),
        "quotes_bad": sum(int(b) - int(a) for a, b in quotes),
        "calls": sum(r["calls"] for r in rows) / n,
        "chars": sum(r["evidence_chars"] for r in rows) / n,
        "s": sum(r["latency_s"] for r in rows) / n,
    }


def spread(values: list[float], fmt: str) -> str:
    """Mean, and the range across runs when there is more than one."""
    mean = sum(values) / len(values)
    if len(values) == 1 or min(values) == max(values):
        return format(mean, fmt)
    return f"{format(mean, fmt)} ({format(min(values), fmt)}–{format(max(values), fmt)})"


def counted(names: list[str]) -> str:
    tally: dict[str, int] = {}
    for name in names:
        tally[name] = tally.get(name, 0) + 1
    return ", ".join(f"{n} ×{c}" if c > 1 else n for n, c in sorted(tally.items(), key=lambda kv: -kv[1])) or "-"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--techniques", default="bm25,dense,dci")
    ap.add_argument("--runs", type=int, default=3, help="runs per case; the model does not answer the same way twice")
    ap.add_argument("--only", help="run one case id")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    from helpers import config
    cfg = config.from_env(ROOT)

    pages = load_pages()
    chunks = build_chunks(pages)
    cases = load_cases()
    if args.only:
        cases = [c for c in cases if c["id"] == args.only]

    twins = twin_groups(pages)
    results: dict[str, list[list[dict]]] = {}   # technique -> runs -> rows
    details = []
    for technique in args.techniques.split(","):
        if technique == "dci":
            tools, funcs = dci_tools(pages), make_dci(pages)
        else:
            tools, funcs = SEARCH_TOOLS, {"search_chunks": make_search(chunks, technique)}
        results[technique] = []
        for run in range(1, args.runs + 1):
            rows = []
            for case in cases:
                result = run_agent(cfg, case["question"], tools, funcs)
                row = score(case, result, twins)
                rows.append(row)
                details.append({"technique": technique, "run": run, **row, "question": case["question"],
                                "gold": case["gold"], **result})
                print(f"{technique} run {run} {row['id']}: {'pass' if row['pass'] else 'FAIL'}  found {row['found']}  "
                      f"wrong {len(row['wrong'])}  calls {row['calls']}  {row['latency_s']}s")
            results[technique].append(rows)

    n_answerable = sum(c["kind"] != "decline" for c in cases)
    n_declines = len(cases) - n_answerable
    lines = [
        "# AI-1 step 1, model + tools (Agentic RAG and DCI)",
        "",
        f"Model: `{cfg.llm_model}`. bm25/dense: {len(chunks)} chunks from {len(pages)} wiki pages (split at `##`); "
        f"dci: the {len(pages)} pages and the index. Max {MAX_TURNS} turns, k capped at {MAX_K}. "
        f"**{args.runs} runs per case**: each cell is the mean, with the range across runs in brackets. "
        "Twins (the same skill under two categories) count as one gold skill: either passes.",
        "",
        f"| technique | all gold found (of {n_answerable}) | gold recall | wrong named | declines correct (of {n_declines}) "
        "| quotes not in her text | calls | evidence chars | s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for technique, runs in results.items():
        sums = [run_summary(rows) for rows in runs]
        col = lambda key: [x[key] for x in sums]  # noqa: E731
        lines.append(
            f"| {technique} | {spread(col('all_found'), '.1f')} | {spread(col('recall'), '.0%')} | "
            f"{spread(col('wrong'), '.1f')} | {spread(col('declines'), '.1f')} | {spread(col('quotes_bad'), '.1f')} | "
            f"{spread(col('calls'), '.1f')} | {spread(col('chars'), ',.0f')} | {spread(col('s'), '.1f')} |")
    for technique, runs in results.items():
        lines += [
            "",
            f"## {technique}",
            "",
            "| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for i, case in enumerate(cases):
            per_case = [rows[i] for rows in runs]
            k = len(per_case)
            lines.append(
                f"| {case['id']} | {case['kind']} | {sum(r['pass'] for r in per_case)}/{k} | "
                f"{counted([m for r in per_case for m in r['missed']])} | "
                f"{counted([w for r in per_case for w in r['wrong']])} | "
                f"{sum(r['calls'] for r in per_case) / k:.1f} | "
                f"{sum(r['evidence_chars'] for r in per_case) / k:,.0f} | {sum(r['latency_s'] for r in per_case) / k:.1f} |")
    if not args.only:
        OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        OUT_JSONL.write_text("".join(json.dumps(d) + "\n" for d in details), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
