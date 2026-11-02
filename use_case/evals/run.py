"""The whole interface: run the AI-1 eval and print the report.

    uv run python use_case/evals/run.py              # echo, oracle and the live endpoint
    uv run python use_case/evals/run.py --replay     # the recorded traces instead of the live endpoint

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
from harness import SCORERS, echo, endpoint, load_cases, make_oracle, make_replay  # noqa: E402


def table(reports) -> str:
    names = list(SCORERS)
    lines = ["| system | n | " + " | ".join(names) + " |", "| --- | --- | " + " | ".join("---" for _ in names) + " |"]
    for r in reports:
        lines.append(f"| {r.name} | {r.n} | " + " | ".join(f"{r.means[s]:.2f}" for s in names) + " |")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", action="store_true", help="score traces.jsonl instead of calling the endpoint")
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
        h.run(cases, system, SCORERS, name=name),
    ]
    print(table(reports))
    for r in reports:
        if r.errors:
            print(f"\n{r.name}: {r.errors} cases raised; see their `error` in the report")


if __name__ == "__main__":
    main()
