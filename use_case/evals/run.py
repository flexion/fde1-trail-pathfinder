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
import json
import sys
from datetime import date
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
# The summary the demo page shows under the AI-1 screen (app.py serves it at /eval).
SUMMARY = ROOT / "01_Product_Engineering" / "challenge" / "data" / "eval.json"

# Plain words for each scorer, and the failures.md line it traces to.
LABELS = {
    "judge_related": ("Every pre-checked skill is backed by her words", "lines 5 and 6, scored by a judge model"),
    "valid_output": ("Well-formed: real ids, verbatim quotes, no raised level without a rubric line", "guards"),
    "declines_when_it_should": ("Declines exactly when it should", "guards"),
    "decline_wording": ("A decline never asks for a background she already picked", "line 10"),
    "quote_is_a_phrase": ("Quotes point at the words that matter, not a whole sentence", "line 3"),
    "labelled_by_source": ("Says the model answered when she wrote text", "line 4"),
}


def export_summary(run: h.RunReport, measured: str | None = None) -> Path:
    """Write the numbers the demo page shows: the headline with its interval, and each scorer's mean."""
    measured = measured or run.meta.get("measured")
    headline = run.meta["headline"]
    rows = [
        {"id": name, "label": LABELS[name][0], "traces_to": LABELS[name][1], "value": round(run.means[name], 3)}
        for name in [headline, *SCORERS]
    ]
    summary = {
        "measured": measured,
        "n": run.n,
        "system": run.meta.get("system", run.name),
        "headline": {**rows[0], "ci": run.meta.get("headline_ci")},
        "scorers": rows[1:],
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return SUMMARY


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
    ap.add_argument("--export", action="store_true", help="only rewrite the demo page's eval.json from baseline.json")
    ap.add_argument("--measured", help="the date to stamp with --export when baseline.json has none (YYYY-MM-DD)")
    args = ap.parse_args()

    if args.export:
        out = export_summary(h.load(BASELINE), args.measured)
        print(f"wrote {out.relative_to(ROOT)}")
        return

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
    run.meta["measured"] = date.today().isoformat()
    if args.save:
        h.save(run, BASELINE)
        print(f"saved {BASELINE.relative_to(ROOT)}")
        print(f"wrote {export_summary(run).relative_to(ROOT)}")
    if BASELINE.exists():
        print(h.compare(h.load(BASELINE), run))


if __name__ == "__main__":
    main()
