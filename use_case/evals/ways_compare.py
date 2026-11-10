"""TC5 Steps 4 and 5: the tool loop and the skill, on the same requests, measured.

    uv run python use_case/evals/ways_compare.py            # Step 4 and Step 5, 3 runs each
    uv run python use_case/evals/ways_compare.py --runs 1   # quicker

Writes ways_results.jsonl (one row per run) and ways_results.md (medians and ranges).

Each run goes through suggest() in-process, the same code as the API, with the way chosen
per call. Per run: model calls, capability calls counted two ways (an in-process counting
wrapper passed as `search=`, and the skill's far-side stderr lines), tool calls on the
first model turn, wall-clock, tokens, and what came back.

Step 4 leaves k to the model (tool) and to run.py's default (skill). Step 5 forces the
payload size: k=1, 4 and 8 for both ways on the multi-topic request.

Needs a model in .env and the wiki in use_case/data/wiki (see run.py's docstring).
"""

from __future__ import annotations

import argparse
import json
import logging
import statistics
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHALLENGE = ROOT / "01_Product_Engineering" / "challenge"
load_dotenv(ROOT / ".env", override=True)
sys.path.insert(0, str(CHALLENGE))

from schema import Confidence, ExperienceRequest  # noqa: E402
from suggest import CapabilityCounter, Meter, search_chunks, suggest  # noqa: E402

REQUESTS = {
    "t-ai1-01": "single topic, with a chip",
    "t-ai1-13": "multi-topic, no chip",
}
MULTI = "t-ai1-13"
WAYS = ("tool", "skill")
SWEEP_K = (1, 4, 8)
OUT_JSONL = HERE / "ways_results.jsonl"
OUT_MD = HERE / "ways_results.md"


class Failures(logging.Handler):
    """suggest() falls back to the rules on any failure; a measurement must not mistake that for an answer."""

    def __init__(self):
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def counting_search(sink: dict, force_k: int | None):
    """search_chunks behind a counter: what Step 4 means by the capability taking its function as an argument."""

    def search(query: str, k: int = 4) -> str:
        sink["calls"] += 1
        sink["asked_k"].append(k)
        result = search_chunks(query, force_k or k)
        sink["bytes"].append(len(result.encode()))
        sink["queries"].append(query)
        return result

    return search


def run_once(way: str, rid: str, case_input: dict, force_k: int | None, step: str) -> dict:
    meter, far = Meter(), CapabilityCounter()
    sink = {"calls": 0, "asked_k": [], "bytes": [], "queries": []}
    measure = {"meter": meter}
    if way == "tool":
        measure["search"] = counting_search(sink, force_k)
    else:
        measure["counter"] = far
        if force_k:
            measure["k"] = force_k
    failures = Failures()
    logging.getLogger("suggest").addHandler(failures)
    started = time.perf_counter()
    try:
        result = suggest(ExperienceRequest.model_validate(case_input), way=way, **measure)
    finally:
        latency_ms = round(1000 * (time.perf_counter() - started))
        logging.getLogger("suggest").removeHandler(failures)
    model_sugs = [s for s in result.suggestions if s.reason.startswith("You wrote")]
    payload = sink["bytes"] if way == "tool" else far.bytes
    return {
        "step": step, "way": way, "request": rid, "k": force_k or "default",
        "model_calls": meter.calls,
        "capability_calls_in_process": sink["calls"],
        "capability_calls_far_side": far.calls if way == "skill" else None,
        "first_turn_tool_calls": meter.first_turn_tool_calls,
        "tool_calls_emitted": meter.tool_calls_emitted,
        "latency_ms": latency_ms,
        "prompt_tokens": meter.prompt_tokens, "completion_tokens": meter.completion_tokens,
        "total_tokens": meter.total_tokens,
        "payload_bytes_per_call": payload,
        "payload_bytes_total": sum(payload),
        "model_asked_k": sink["asked_k"] if way == "tool" else None,
        "queries": sink["queries"] if way == "tool" else None,
        "suggestions": len(result.suggestions),
        "declined": result.declined,
        "produced_by": result.produced_by,
        "response_bytes": len(result.model_dump_json().encode()),
        "text_skill_ids": sorted(s.skill_id for s in model_sugs),
        "prechecked_ids": sorted(s.skill_id for s in result.suggestions if s.confidence != Confidence.CHECK),
        "notes": meter.notes,
        "error": "; ".join(failures.messages) or None,
    }


def med(rows: list[dict], key: str) -> str:
    vals = [r[key] for r in rows if isinstance(r[key], (int, float))]
    if not vals:
        return "n/a"
    m = statistics.median(vals)
    m = int(m) if m == int(m) else round(m, 1)
    return f"{m} ({min(vals)}–{max(vals)})" if min(vals) != max(vals) else f"{m}"


def capability_cell(rows: list[dict]) -> str:
    if rows[0]["way"] == "tool":
        return med(rows, "capability_calls_in_process")
    return f"{med(rows, 'capability_calls_in_process')} in-process / {med(rows, 'capability_calls_far_side')} far side"


def agreement(rows: list[dict]) -> list[str]:
    lines = []
    for rid in REQUESTS:
        sets = {}
        for way in WAYS:
            runs = [r for r in rows if r["step"] == "step4" and r["request"] == rid and r["way"] == way]
            sets[way] = {"text": [tuple(r["text_skill_ids"]) for r in runs],
                         "pre": [tuple(r["prechecked_ids"]) for r in runs]}
        for way in WAYS:
            uniq = sorted(set(sets[way]["text"]))
            lines.append(f"- `{rid}` {way}: text-path skill ids per run "
                         + "; ".join(f"`{', '.join(u) or '(none)'}` ×{sets[way]['text'].count(u)}" for u in uniq))
            uniq_pre = sorted(set(sets[way]["pre"]))
            lines.append(f"  pre-checked: "
                         + "; ".join(f"`{', '.join(u) or '(none)'}` ×{sets[way]['pre'].count(u)}" for u in uniq_pre))
        every = {w: set.intersection(*map(set, sets[w]["text"])) if sets[w]["text"] else set() for w in WAYS}
        anyrun = {w: set().union(*map(set, sets[w]["text"])) for w in WAYS}
        lines.append(f"  **{rid}**: in every run, tool `{', '.join(sorted(every['tool'])) or '—'}`, skill "
                     f"`{', '.join(sorted(every['skill'])) or '—'}`. In some run of one way only: tool "
                     f"`{', '.join(sorted(anyrun['tool'] - anyrun['skill'])) or '—'}`, skill "
                     f"`{', '.join(sorted(anyrun['skill'] - anyrun['tool'])) or '—'}`.")
    return lines


def report(rows: list[dict]) -> str:
    out = ["# TC5: the tool loop vs the skill, measured", "",
           f"Measured {time.strftime('%Y-%m-%d')} by `ways_compare.py`, in-process through `suggest()`, model "
           "`LLM_MODEL` from `.env` through the gateway. Median of the runs, range in brackets. "
           "Tokens are everything that crossed the model boundary (prompt + completion, all calls).", "",
           "Requests: `t-ai1-01` is one kind of work (hand trail work on a corps crew) with the `corps` chip. "
           "`t-ai1-13` is the multi-topic one, chosen over `t-ai1-03` because it names four unrelated kinds "
           "of work (volunteer coordination, a newsletter, a grant, drain clearing and brushing) and no chip, so "
           "every skill has to come from searches; `t-ai1-03`'s saw work and supervision overlap and its "
           "`forestry` chip supplies skills with no search.", "",
           "Capability calls: the tool way's count is a counting wrapper passed as `search=`. The skill way's "
           "in-process count is the same wrapper's view (it never runs); the far-side count is the "
           "`capability_call search_chunks` lines `run.py` prints on stderr.", "",
           "## Step 4: demo scale (k left to the model / run.py default)", "",
           "| way | request | model calls | capability calls | tool calls on turn 1 | latency ms | tokens | "
           "payload bytes in context | suggestions | declined | response bytes | errors |",
           "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for rid in REQUESTS:
        for way in WAYS:
            rs = [r for r in rows if r["step"] == "step4" and r["request"] == rid and r["way"] == way]
            if not rs:
                continue
            errs = sum(1 for r in rs if r["error"])
            out.append(f"| {way} | {rid} | {med(rs, 'model_calls')} | {capability_cell(rs)} | "
                       f"{med(rs, 'first_turn_tool_calls')} | {med(rs, 'latency_ms')} | {med(rs, 'total_tokens')} | "
                       f"{med(rs, 'payload_bytes_total')} | {med(rs, 'suggestions')} | "
                       f"{sum(r['declined'] for r in rs)}/{len(rs)} | {med(rs, 'response_bytes')} | {errs}/{len(rs)} |")
    out += ["", "Turn 1 for the skill way is the plan call, which must emit exactly one `plan_searches` call; "
            "the number of searches it planned is the far-side capability count.", "",
            f"## Step 5: payload size, `{MULTI}`, k forced", "",
            "| way | k | bytes per search (median) | capability calls | model calls | prompt tokens | tokens | latency ms |",
            "| --- | --- | --- | --- | --- | --- | --- | --- |"]
    for k in SWEEP_K:
        for way in WAYS:
            rs = [r for r in rows if r["step"] == "step5" and r["way"] == way and r["k"] == k]
            if not rs:
                continue
            per = [b for r in rs for b in r["payload_bytes_per_call"]]
            out.append(f"| {way} | {k} | {int(statistics.median(per)) if per else 'n/a'} | {capability_cell(rs)} | "
                       f"{med(rs, 'model_calls')} | {med(rs, 'prompt_tokens')} | {med(rs, 'total_tokens')} | "
                       f"{med(rs, 'latency_ms')} |")
    out += ["", "## Did the two ways suggest the same skills? (Step 4 runs)", "", *agreement(rows), ""]
    queries = sorted({q for r in rows if r["queries"] for q in r["queries"]})
    if queries:
        sizes = sorted(len(search_chunks(q, 4).encode()) for q in queries)
        out += ["## Real response size: the queries the tool loop actually sent, re-run at k=4", "",
                f"{len(queries)} distinct queries; one `search_chunks` response is {sizes[0]}–{sizes[-1]} bytes, "
                f"median {int(statistics.median(sizes))}. Chunks are cut at 1,000 characters, so k=8 is at most "
                "about 8 KB.", "",
                "Skill-way latency is mostly process start, not the boundary itself: a `run.py` whose query "
                "embedding is cached takes about 0.2 s; one with a new query imports litellm, calls Titan and "
                "rewrites the 5 MB `EMBED_CACHE` file, about 4.5 s, every time, in a fresh process.", ""]
    return "\n".join(out)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--report", action="store_true", help="rewrite the md from the jsonl, no model calls")
    args = parser.parse_args()
    if args.report:
        OUT_MD.write_text(report([json.loads(line) for line in OUT_JSONL.read_text().splitlines() if line.strip()]))
        return
    inputs = {json.loads(line)["id"]: json.loads(line)["input"]
              for line in (HERE / "trace_inputs.jsonl").read_text().splitlines() if line.strip()}
    plan = [("step4", way, rid, None) for rid in REQUESTS for way in WAYS]
    plan += [("step5", way, MULTI, k) for k in SWEEP_K for way in WAYS]
    rows = []
    with OUT_JSONL.open("w") as f:
        for step, way, rid, k in plan:
            for n in range(args.runs):
                row = run_once(way, rid, inputs[rid], k, step)
                rows.append(row)
                f.write(json.dumps(row) + "\n")
                f.flush()
                print(f"{step} {way:5} {rid} k={row['k']} run {n + 1}: {row['model_calls']} model calls, "
                      f"{row['capability_calls_in_process']}/{row['capability_calls_far_side']} capability, "
                      f"{row['total_tokens']} tokens, {row['latency_ms']} ms"
                      + (f"  ERROR {row['error']}" if row["error"] else ""), flush=True)
    OUT_MD.write_text(report(rows))
    print(f"wrote {OUT_JSONL.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
