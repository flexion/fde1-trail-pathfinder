"""The whole interface: run the AI-1 eval and print the report.

    uv run python use_case/evals/run.py              # echo, oracle and the live endpoint, compared to baseline.json
    uv run python use_case/evals/run.py --replay     # the recorded traces instead of the live endpoint
    uv run python use_case/evals/run.py --save       # also write the endpoint run to baseline.json

Echo and oracle run the code scorers; the judge's own check on them is check_judge.py.
The endpoint run adds the judge, and the headline (the judge) gets a 95% interval.

The live endpoint needs a model in .env and the skills wiki in use_case/data/wiki
(git-ignored; use_case/fetch_trailskills_levels.py then use_case/build_wiki.py).
Without the wiki it still answers, from the keyword rules.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from helpers import harness as h  # noqa: E402
from harness import (HEADLINE, SCORERS, bootstrap_ci, echo, endpoint, judge_related, load_cases,  # noqa: E402
                     make_oracle, make_replay)

BASELINE = HERE / "baseline.json"


def table(reports) -> str:
    names = [*SCORERS, HEADLINE]
    lines = ["| system | n | " + " | ".join(names) + " |", "| --- | --- | " + " | ".join("---" for _ in names) + " |"]
    for r in reports:
        cells = (f"{r.means[s]:.2f}" if s in r.means else "-" for s in names)
        lines.append(f"| {r.name} | {r.n} | " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true", help="score traces.jsonl instead of calling the endpoint")
    ap.add_argument("--save", action="store_true", help="write the endpoint run to baseline.json")
    args = ap.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    import litellm

    litellm.suppress_debug_info = True

    cases = load_cases()
    system = make_replay(HERE / "traces.jsonl") if args.replay else endpoint
    name = "endpoint (replay)" if args.replay else "endpoint"
    reports = [
        h.run(cases, echo, SCORERS, name="echo"),
        h.run(cases, make_oracle(cases), SCORERS, name="oracle"),
        h.run(cases, system, {**SCORERS, HEADLINE: judge_related}, name=name,
              meta={"headline": HEADLINE, "system": name}),
    ]
    print(table(reports))
    for r in reports:
        if r.errors:
            print(f"\n{r.name}: {r.errors} cases raised; see their `error` in the report")

    run = reports[-1]
    low, high = bootstrap_ci([res.scores[HEADLINE] for res in run.results])
    print(f"\nHeadline {HEADLINE}: {run.means[HEADLINE]:.2f}, 95% CI [{low:.2f}, {high:.2f}], n={run.n}")
    run.meta["headline_ci"] = [round(low, 3), round(high, 3)]
    if args.save:
        h.save(run, BASELINE)
        print(f"saved {BASELINE.relative_to(ROOT)}")
    if BASELINE.exists():
        print(h.compare(h.load(BASELINE), run))


if __name__ == "__main__":
    main()
