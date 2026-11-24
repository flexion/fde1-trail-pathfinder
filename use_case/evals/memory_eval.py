"""TC7: tests that target the procedural memory directly, not the app around it.

    uv run python use_case/evals/memory_eval.py             # offline tests, then the live ones (3 pairs per request)
    uv run python use_case/evals/memory_eval.py --offline   # staleness and leakage only: no model, no wiki
    uv run python use_case/evals/memory_eval.py --runs 1

Offline (run.py runs these too, every time):
1. Staleness. Write a procedure, write a new one for the same subject: only the new one comes
   back, and only one row is live. A procedure learned against another wiki is not returned.
2. Leakage. There are no logins, but the memory is shared by every visitor, so visitor B gets
   what visitor A taught it. Assert a row can only ever hold ids: nothing of A's text is
   stored, and anything that is not an id is refused on write.

Live (needs a model in .env and the wiki):
3. Cost. The same request twice on an empty store: attempt two must cost fewer tokens and
   fewer searches (median over the pairs; one pair varies too much to say anything).
4. Truthfulness. On attempt two the model says, per skill, whether it matched a remembered
   section or a searched one. That is its account. The log is what the store handed it and
   what each search returned, recorded outside the model. Score the share of claims the log
   supports.
And the check the README asks for: does memory make the answer worse? The text-path skills
on attempt two are compared to attempt one.

Writes memory_results.jsonl and memory_results.md.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CHALLENGE = ROOT / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(CHALLENGE))

REQUESTS = ("t-ai1-01", "t-ai1-03", "t-ai1-05", "t-ai1-13")
OUT_JSONL = HERE / "memory_results.jsonl"
OUT_MD = HERE / "memory_results.md"
VERSION_A, VERSION_B = "a" * 16, "b" * 16
HER_TEXT = ("For three years I coordinated volunteers for our local trail club. I ran the work-day sign-ups, "
            "wrote the monthly newsletter, and helped write a state grant for new trail signs.")


def words(text: str) -> list[str]:
    return re.findall(r"[a-z']+", text.lower())


def trigrams(text: str) -> set[tuple[str, ...]]:
    w = words(text)
    return {tuple(w[i:i + 3]) for i in range(len(w) - 2)}


# --- offline ------------------------------------------------------------------------------


def test_staleness() -> list[str]:
    from procedures import Procedures

    problems = []
    store = Procedures()
    store.write("funding-grants", VERSION_A, ["funding-grants#entry"])
    store.write("funding-grants", VERSION_A, ["funding-grants#expert"])
    got = store.recall("funding-grants", VERSION_A)
    if got != ["funding-grants#expert"]:
        problems.append(f"after a second write, recall gave {got}, not only the new value")
    if "funding-grants#entry" in got:
        problems.append("the superseded value came back")
    live = [r for r in store.rows() if r["subject"] == "funding-grants" and r["superseded_at"] is None]
    if len(live) != 1:
        problems.append(f"{len(live)} live rows for one subject")
    if store.recall("funding-grants", VERSION_B):
        problems.append("a procedure learned against another wiki version came back")
    return problems


def test_leakage() -> list[str]:
    """Visitor A's request goes through the real write path; nothing of her text may reach a row."""
    import suggest
    from procedures import Procedures
    from schema import Confidence

    problems = []
    store = Procedures()
    sentences = [s for s in re.split(r"(?<=\.)\s+", HER_TEXT) if s]
    trace = {"subjects": {sentences[0]: "crew-management", sentences[1]: "funding-grants"},
             "recalled": [], "searched": ["crew-management#entry", "funding-grants#entry", "communications#entry"]}
    credited = [suggest.suggestion("crew-management", Confidence.LIKELY, "x", "coordinated volunteers"),
                suggest.suggestion("funding-grants", Confidence.LIKELY, "x", "helped write a state grant")]
    real_version = suggest.wiki_version
    suggest.wiki_version = lambda: VERSION_A   # no wiki needed offline
    try:
        suggest._remember(HER_TEXT, credited, store, trace)
    finally:
        suggest.wiki_version = real_version
    rows = store.rows()
    if not rows:
        problems.append("the write path stored nothing, so this test proves nothing")
    stored = json.dumps(rows)
    leaked = trigrams(HER_TEXT) & trigrams(stored.replace("-", " ").replace("#", " "))
    if leaked:
        problems.append(f"her words reached a row: {sorted(' '.join(t) for t in leaked)}")
    # What visitor B receives is recall's output: ids only, so only wiki text can follow.
    for row in rows:
        for chunk in store.recall(row["subject"], VERSION_A):
            if not re.match(r"^[a-z0-9-]+#[a-z0-9-]+$", chunk):
                problems.append(f"recall returned a non-id {chunk!r}")
    # The gate itself: her text, or a model query that copies it, is refused.
    for bad in (["work-day sign-ups volunteer management"], [HER_TEXT], ["funding-grants#entry", "her words"]):
        try:
            store.write("funding-grants", VERSION_A, bad)
            problems.append(f"write accepted {bad!r}")
        except ValueError:
            pass
    try:
        store.write(sentences[0], VERSION_A, ["crew-management#entry"])
        problems.append("write accepted her sentence as a subject")
    except ValueError:
        pass
    return problems


def recall_at_scale(sizes=(10, 100, 1_000)) -> list[dict]:
    """Recall quality and lookup time as the store grows. Each size is filled with that many subjects,
    each rewritten three times (so two thirds of the rows are superseded), then every subject is recalled."""
    from procedures import Procedures

    out = []
    for n in sizes:
        store = Procedures()
        for rewrite in range(3):
            for i in range(n):
                store.write(f"skill-{i}", VERSION_A, [f"skill-{i}#v{rewrite}"])
        started = time.perf_counter()
        right = sum(store.recall(f"skill-{i}", VERSION_A) == [f"skill-{i}#v2"] for i in range(n))
        per_ms = 1000 * (time.perf_counter() - started) / n
        out.append({"live": n, "rows": len(store.rows()), "recall": right / n, "ms_per_recall": round(per_ms, 3)})
    return out


def offline() -> dict[str, list[str]]:
    return {"staleness": test_staleness(), "leakage": test_leakage()}


# --- live ---------------------------------------------------------------------------------


def run_pair(case_input: dict) -> list[dict]:
    """The same request twice on an empty store: what each attempt cost and what it said."""
    import suggest
    from procedures import Procedures
    from schema import ExperienceRequest

    store, out = Procedures(), []
    for attempt in (1, 2):
        meter, trace, searches = suggest.Meter(), {}, {"n": 0}

        def search(query: str, k: int = 4) -> str:
            searches["n"] += 1
            return suggest.search_chunks(query, k)

        started = time.perf_counter()
        result = suggest.suggest(ExperienceRequest.model_validate(case_input), way="tool", meter=meter,
                                 memory=store, trace=trace, search=search)
        out.append({
            "attempt": attempt, "model_calls": meter.calls, "searches": searches["n"],
            "tokens": meter.total_tokens, "latency_ms": round(1000 * (time.perf_counter() - started)),
            "produced_by": result.produced_by,
            "text_skills": sorted(s.skill_id for s in result.suggestions if s.reason.startswith("You wrote")),
            "recalled": trace.get("recalled", []), "searched": trace.get("searched", []),
            "claims": trace.get("claims", []), "written": trace.get("written", {}),
        })
    return out


def truthful(row: dict) -> tuple[int, int, int]:
    """(claims the log supports, claims it contradicts, claims with no source) for one attempt."""
    from suggest import _twin

    def skills(ids):
        return {_twin(c.split("#")[0]) for c in ids}

    remembered, searched = skills(row["recalled"]), skills(row["searched"])
    ok = bad = missing = 0
    for sid, source in row["claims"]:
        if source not in ("remembered", "searched"):
            missing += 1
        elif _twin(sid) in (remembered if source == "remembered" else searched):
            ok += 1
        else:
            bad += 1
    return ok, bad, missing


def med(vals: list) -> float:
    return statistics.median(vals) if vals else float("nan")


def report(rows: list[dict], offline_problems: dict[str, list[str]], runs: int) -> str:
    out = ["# TC7: procedural memory, tested directly", "",
           f"Measured {time.strftime('%Y-%m-%d')} by `memory_eval.py`, {runs} pair(s) per request, each pair on an "
           "empty store, tool way, `LLM_MODEL` from `.env`. Median of the pairs, range in brackets.", "",
           "## Offline (no model, no wiki; `run.py` runs these too)", "",
           "| test | result |", "| --- | --- |"]
    for name, problems in offline_problems.items():
        out.append(f"| {name} | {'PASS' if not problems else 'FAIL: ' + '; '.join(problems)} |")
    out += ["", "## Recall at 10, 100 and 1,000 entries", "",
            "| live entries | rows (incl. superseded) | recall | ms per recall |", "| --- | --- | --- | --- |"]
    out += [f"| {r['live']} | {r['rows']} | {r['recall']:.2f} | {r['ms_per_recall']} |" for r in recall_at_scale()]
    out += ["", "The store is an exact lookup on an indexed key, not a search, so it cannot rank the wrong entry "
            "first and recall stays 1.00 as it grows. FTS is not used and is not needed. Where recall can go "
            "wrong is the key itself: `subject_of` picks the skill the wiki index ranks first for a sentence, and "
            "two wordings of the same work can land on different subjects (a miss, not a wrong entry). That is "
            "what the cost table below measures in practice.", ""]
    out += ["", "## Cost: attempt one vs attempt two", "",
            "| request | tokens 1 → 2 | searches 1 → 2 | model calls 1 → 2 | latency ms 1 → 2 | cheaper? |",
            "| --- | --- | --- | --- | --- | --- |"]

    def cell(rs, key):
        vals = [r[key] for r in rs]
        m = med(vals)
        m = int(m) if m == int(m) else round(m, 1)
        return f"{m} ({min(vals)}–{max(vals)})" if min(vals) != max(vals) else f"{m}"

    all_ok = True
    for rid in REQUESTS:
        one = [r for r in rows if r["request"] == rid and r["attempt"] == 1]
        two = [r for r in rows if r["request"] == rid and r["attempt"] == 2]
        if not one:
            continue
        cheaper = med([r["tokens"] for r in two]) < med([r["tokens"] for r in one]) and \
            med([r["searches"] for r in two]) < med([r["searches"] for r in one])
        all_ok &= cheaper
        out.append(f"| {rid} | {cell(one, 'tokens')} → {cell(two, 'tokens')} | {cell(one, 'searches')} → "
                   f"{cell(two, 'searches')} | {cell(one, 'model_calls')} → {cell(two, 'model_calls')} | "
                   f"{cell(one, 'latency_ms')} → {cell(two, 'latency_ms')} | {'yes' if cheaper else '**no**'} |")
    t1 = [r["tokens"] for r in rows if r["attempt"] == 1]
    t2 = [r["tokens"] for r in rows if r["attempt"] == 2]
    out += ["", f"**Cost test: {'PASS' if all_ok else 'FAIL'}.** Median tokens over every pair: "
            f"{int(med(t1))} → {int(med(t2))} ({100 * (1 - med(t2) / med(t1)):.0f}% fewer)."]

    ok = bad = missing = 0
    for r in rows:
        if r["attempt"] == 2:
            a, b, m = truthful(r)
            ok, bad, missing = ok + a, bad + b, missing + m
    total = ok + bad + missing
    out += ["", "## Truthfulness: the model's account vs the log (attempt two)", "",
            f"{total} skill claims. The log supports **{ok}**, contradicts **{bad}**, and **{missing}** gave no source. "
            f"Truthfulness: **{ok / total:.2f}**." if total else "No claims on attempt two.", "",
            "A contradiction is a skill the model said it matched in a remembered section when no remembered "
            "section was about that skill (or said it searched when no search returned it).", "",
            "## Does memory make the answer worse? Text-path skills, attempt one vs two", "",
            "| request | pair | attempt one | attempt two | lost on two | gained on two |",
            "| --- | --- | --- | --- | --- | --- |"]
    for rid in REQUESTS:
        pairs = [r for r in rows if r["request"] == rid]
        for n in range(0, len(pairs), 2):
            a, b = pairs[n], pairs[n + 1]
            lost, gained = sorted(set(a["text_skills"]) - set(b["text_skills"])), sorted(set(b["text_skills"]) - set(a["text_skills"]))
            out.append(f"| {rid} | {n // 2 + 1} | {len(a['text_skills'])} | {len(b['text_skills'])} | "
                       f"{', '.join(lost) or '—'} | {', '.join(gained) or '—'} |")
    return "\n".join(out) + "\n"


def main() -> None:
    from dotenv import load_dotenv

    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--offline", action="store_true", help="staleness and leakage only")
    ap.add_argument("--report", action="store_true", help="rewrite the md from the jsonl, no model calls")
    args = ap.parse_args()
    problems = offline()
    for name, found in problems.items():
        print(f"{name}: {'PASS' if not found else 'FAIL ' + '; '.join(found)}")
    if args.offline:
        sys.exit(1 if any(problems.values()) else 0)
    if args.report:
        rows = [json.loads(line) for line in OUT_JSONL.read_text().splitlines() if line.strip()]
        OUT_MD.write_text(report(rows, problems, len(rows) // (2 * len(REQUESTS))))
        return
    load_dotenv(ROOT / ".env", override=True)
    inputs = {json.loads(line)["id"]: json.loads(line)["input"]
              for line in (HERE / "trace_inputs.jsonl").read_text().splitlines() if line.strip()}
    rows = []
    with OUT_JSONL.open("w") as f:
        for rid in REQUESTS:
            for n in range(args.runs):
                for row in run_pair(inputs[rid]):
                    row = {"request": rid, "pair": n + 1, **row}
                    rows.append(row)
                    f.write(json.dumps(row) + "\n")
                    f.flush()
                    print(f"{rid} pair {n + 1} attempt {row['attempt']}: {row['tokens']} tokens, {row['searches']} "
                          f"searches, {row['model_calls']} calls, skills {row['text_skills']}", flush=True)
    OUT_MD.write_text(report(rows, problems, args.runs))
    print(f"wrote {OUT_JSONL.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
