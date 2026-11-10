"""Week 5 fair question #4: when her text and her chips disagree, does the text win?

    uv run python use_case/evals/conflict_eval.py             # live endpoint, 3 runs per case
    uv run python use_case/evals/conflict_eval.py --runs 1
    uv run python use_case/evals/conflict_eval.py --oracle    # scorer check, no model calls

A separate slice, not part of `run.py`, so baseline.json keeps comparing like with like.
Each case runs several times because the tool loop is not deterministic; a case's score
is the share of runs that passed.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from harness import (conflict_problems, endpoint, found_skills, load_conflict_cases, load_missed_cases,
                     make_oracle, text_beats_chips)  # noqa: E402


def oracle_answer(case: dict, *, wrong: bool = False) -> str:
    """A hand-built answer that satisfies the label (proves the scorer can say yes). With
    `wrong`, it pre-checks every skill the label says must not be, instead (proves it can say no)."""
    from harness import framework

    expect = case["output"]
    wanted = expect.get("present", []) + expect.get("still_prechecked", [])
    ids = expect.get("not_prechecked", []) if wrong else [i if isinstance(i, str) else i[0] for i in wanted]
    comps = {c["id"]: c for c in framework()["competencies"]}
    sug = [{"skill_id": i, "category": comps[i]["category"], "skill": comps[i]["name"], "level": "Entry",
            "confidence": "possible", "reason": "oracle", "quote": None} for i in ids]
    return json.dumps({"declined": not sug, "suggestions": sug, "reason": "oracle" if not sug else None, "produced_by": "model"})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--oracle", action="store_true", help="score hand-built answers; no model calls")
    args = ap.parse_args()
    cases = load_conflict_cases()

    if args.oracle:
        golden = make_oracle(load_missed_cases())
        print("found_skills, golden answer as the system:",
              {c["id"]: found_skills(golden(c["input"]), c) for c in load_missed_cases()})
        for case in cases:
            good = text_beats_chips(oracle_answer(case), case)
            bad = text_beats_chips(oracle_answer(case, wrong=True), case)
            print(f"{case['id']}  {case['kind']:<28} right answer {good:.0f}   wrong answer {bad:.0f}")
        return

    load_dotenv(ROOT / ".env", override=True)
    rows = []
    for case in cases:
        scores = []
        print(f"{case['id']}  {case['kind']}")
        for n in range(args.runs):
            actual = endpoint(case["input"])
            problems = conflict_problems(actual, case)
            scores.append(text_beats_chips(actual, case))
            got = json.loads(actual)
            shown = ", ".join(f"{s['skill_id']}:{s['confidence']}" for s in got["suggestions"]) or "declined"
            print(f"   run {n + 1}: {'pass' if not problems else 'FAIL ' + '; '.join(problems)}\n           gave: {shown}")
        rows.append((case, sum(scores) / len(scores)))
        print(f"   -> {sum(scores):.0f}/{len(scores)}\n")
    total = sum(score for _, score in rows) / len(rows)
    print(f"\ntext_beats_chips: {total:.2f} over {len(rows)} cases x {args.runs} runs")

    missed = load_missed_cases()
    print(f"\nfound_skills (recall of skills she described), {len(missed)} golden rows x {args.runs} runs")
    means = []
    for case in missed:
        scores = [found_skills(endpoint(case["input"]), case) for _ in range(args.runs)]
        means.append(sum(scores) / len(scores))
        print(f"   {case['id']}  {means[-1]:.2f}   runs: {', '.join(f'{x:.2f}' for x in scores)}")
    print(f"found_skills: {sum(means) / len(means):.2f}")


if __name__ == "__main__":
    main()
