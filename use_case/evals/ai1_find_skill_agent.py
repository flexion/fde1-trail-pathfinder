"""AI-1 step 1 as Session 5's Agentic RAG: the model searches the wiki and names the skills.

    uv run --group week3 python use_case/evals/ai1_find_skill_agent.py
    uv run --group week3 python use_case/evals/ai1_find_skill_agent.py --techniques dense --only retrieval-03

ai1_find_skill.py scores the ranked pages with no model. This one gives the model
Session 5's `search_chunks` tool over the same wiki and asks it which skills her
words support, each with the words of hers it rests on. Levels are step 2.
The loop and prompt are the same for every technique; only the ranking behind
`search_chunks` changes (bm25 or dense, from ai1_find_skill.py).

Chunks: each page split at `##` (Definition, Entry, Full Performance, Expert),
id `<skill-id>#<section>`, with the skill name and category kept on every chunk so a level
section still says which skill it belongs to (the twins differ only by category).

Scored on retrieval.jsonl, Session 5's columns adapted to skill ids:
    found    gold skills it named / gold skills (twins count as one: either passes)
    wrong    skills it named that are not gold
    quotes   its quotes that are really in her text
    decline  a decline case passes when it declines and names nothing
    calls, evidence chars, latency, how the loop stopped

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
    "Search the wiki with search_chunks before answering; search again with different words "
    "when a task she names has no match yet. A chunk id is <skill-id>#<section>.\n"
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


TOOLS = [{"type": "function", "function": {
    "name": "search_chunks",
    "description": "Search ranked skill-wiki chunks. Search again with a new query when evidence is incomplete.",
    "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "k": {"type": "integer"}},
                   "required": ["query"]}}}]


def run_agent(cfg, question: str, funcs: dict) -> dict:
    """Session 5's loop: call tools until the model answers, at most MAX_TURNS turns."""
    import litellm
    from helpers.llm import complete

    litellm.suppress_debug_info = True

    messages: list[dict] = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    trace: list[dict] = []
    chars = 0
    started = time.perf_counter()
    for _ in range(MAX_TURNS):
        msg = complete(cfg, messages, tools=TOOLS, timeout=120).choices[0].message
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


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--techniques", default="bm25,dense")
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
    results, details = {}, []
    for technique in args.techniques.split(","):
        funcs = {"search_chunks": make_search(chunks, technique)}
        rows = results[technique] = []
        for case in cases:
            result = run_agent(cfg, case["question"], funcs)
            row = score(case, result, twins)
            rows.append(row)
            details.append({"technique": technique, **row, "question": case["question"], "gold": case["gold"], **result})
            print(f"{technique} {row['id']}: {'pass' if row['pass'] else 'FAIL'}  found {row['found']}  "
                  f"wrong {len(row['wrong'])}  calls {row['calls']}  {row['latency_s']}s")

    lines = [
        "# AI-1 step 1, Agentic RAG (search_chunks + model)",
        "",
        f"Model: `{cfg.llm_model}`. {len(chunks)} chunks from {len(pages)} wiki pages (split at `##`). "
        f"Max {MAX_TURNS} turns, k capped at {MAX_K}. One run per case. "
        "Twins (the same skill under two categories) count as one gold skill: either passes.",
        "",
        "| technique | all gold found | gold recall | wrong named | declines correct | quotes ok | avg calls | avg evidence chars | avg s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for technique, rows in results.items():
        answerable = [r for r in rows if r["kind"] != "decline"]
        declines = [r for r in rows if r["kind"] == "decline"]
        found = sum(int(r["found"].split("/")[0]) for r in answerable)
        gold = sum(int(r["found"].split("/")[1]) for r in answerable)
        quotes = [r["quotes_ok"].split("/") for r in rows]
        n = len(rows)
        lines.append(
            f"| {technique} | {sum(r['pass'] for r in answerable)}/{len(answerable)} | {found / max(1, gold):.0%} | "
            f"{sum(len(r['wrong']) for r in rows)} | {sum(r['pass'] for r in declines)}/{len(declines)} | "
            f"{sum(int(a) for a, _ in quotes)}/{sum(int(b) for _, b in quotes)} | "
            f"{sum(r['calls'] for r in rows) / n:.1f} | {sum(r['evidence_chars'] for r in rows) / n:,.0f} | "
            f"{sum(r['latency_s'] for r in rows) / n:.1f} |")
    for technique, rows in results.items():
        lines += [
            "",
            f"## {technique}",
            "",
            "| id | kind | pass | found | missed | wrong | quotes ok | calls | evidence chars | s | stopped |",
            "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
        ]
        for r in rows:
            lines.append(f"| {r['id']} | {r['kind']} | {'pass' if r['pass'] else 'FAIL'} | {r['found']} | "
                         f"{', '.join(r['missed']) or '-'} | {', '.join(r['wrong']) or '-'} | {r['quotes_ok']} | "
                         f"{r['calls']} | {r['evidence_chars']:,} | {r['latency_s']} | {r['stopped']} |")
    if not args.only:
        OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
        OUT_JSONL.write_text("".join(json.dumps(d) + "\n" for d in details), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
