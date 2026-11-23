"""The whole interface: run the AI-1 eval and print the report.

    uv run python use_case/evals/run.py              # echo, oracle and the live endpoint, compared to baseline.json
    uv run python use_case/evals/run.py --replay     # the recorded traces instead of the live endpoint
    uv run python use_case/evals/run.py --save       # also write the endpoint run to baseline.json

Every run starts with the TC7 memory tests that need no model (memory_eval.py: staleness, leakage).
Echo and oracle run the code scorers; the judge's own check on them is check_judge.py.
The endpoint run adds the judge, and the headline (the judge) gets a 95% interval.

The live endpoint needs a model in .env and the skills wiki in use_case/data/wiki
(git-ignored; use_case/fetch_trailskills_levels.py then use_case/build_wiki.py).
Without the wiki it still answers, from the keyword rules.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from helpers import harness as h  # noqa: E402
from harness import (HEADLINE, SCORERS, blocks_injection, bootstrap_ci, echo, endpoint, judge_related,  # noqa: E402
                     load_attack_cases, load_cases, make_oracle, make_replay)

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


class _EvidenceDrops(logging.Handler):
    """Counts suggest's "evidence check dropped ..." log lines (TC6, suggest.backed)."""

    def __init__(self):
        super().__init__(logging.INFO)
        self.messages: list[str] = []
        logging.getLogger("suggest").addHandler(self)
        logging.getLogger("suggest").setLevel(logging.INFO)

    def emit(self, record):
        if record.getMessage().startswith("evidence check dropped"):
            self.messages.append(record.getMessage().removeprefix("evidence check dropped "))


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

    # TC7: the memory's own tests, no model and no wiki, so they run on every eval run.
    from memory_eval import offline as memory_offline

    for name, problems in memory_offline().items():
        print(f"memory {name}: {'PASS' if not problems else 'FAIL ' + '; '.join(problems)}")

    if args.export:
        out = export_summary(h.load(BASELINE), args.measured)
        print(f"wrote {out.relative_to(ROOT)}")
        return

    load_dotenv(ROOT / ".env", override=True)
    import litellm

    litellm.suppress_debug_info = True

    cases = load_cases()
    system = make_replay(HERE / "traces.jsonl") if args.replay else endpoint
    drops = _EvidenceDrops()   # TC6: what the evidence check removed on the live run
    name = "endpoint (replay)" if args.replay else "endpoint"
    reports = [
        h.run(cases, echo, SCORERS, name="echo"),
        h.run(cases, make_oracle(cases), SCORERS, name="oracle"),
        h.run(cases, system, {**SCORERS, HEADLINE: judge_related}, name=name,
              meta={"headline": HEADLINE, "system": name}),
    ]
    print(table(reports))
    if not args.replay:
        print(f"\nevidence check (TC6) dropped {len(drops.messages)} model suggestions across the {len(cases)} cases"
              + "".join(f"\n  {m}" for m in drops.messages))
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
    attack_report()


def attack_report() -> None:
    """Week 6: every winning attack in attacks.jsonl, scored by `blocks_injection` against the
    config that guards its door: direct attacks against the inline rules (no model), attacks in
    the wiki, tool description or SKILL.md against the build-time ladder, whose judge runs on
    INJECTION_MODEL/INJECTION_API_BASE only. Separate from the fifty-case run and baseline.json."""
    from harness import door_config, door_rails
    from rails import injection_judge, stopped_by

    cases = load_attack_cases()
    print("\n## Attacks (Week 6): blocks_injection, by door")
    if not cases:
        print("no attack cases yet: attacks.jsonl has no `winner: true` rows")
        return
    scored = [c for c in cases if door_config(c) == "inline"]
    build = [c for c in cases if door_config(c) == "build"]
    if build:
        # A scorer that raises scores 0 with no message, so reach the judge once first and say why not.
        why = None if injection_judge() else "INJECTION_MODEL/INJECTION_API_BASE is not set"
        if why is None:
            try:
                probe = stopped_by(door_rails("build"), "Two seasons on a trail crew, brushing and building water bars.")
                if probe:
                    why = f"a benign probe was stopped ({probe})"
            except Exception as exc:
                why = f"{type(exc).__name__}: {str(exc)[:160]}"
        if why:
            print(f"skipped {len(build)} judge-dependent cases (wiki, tool, SKILL.md doors), not scored: {why}")
        else:
            scored += build
    if not scored:
        return
    report = h.run(scored, lambda _text: "", {"blocks_injection": blocks_injection}, name="ladder by door")
    for config in ("inline", "build"):
        results = [r for r in report.results if door_config(scored[r.index]) == config]
        if results:
            blocked = sum(r.scores.get("blocks_injection", 0.0) for r in results)
            print(f"{config}: blocked {blocked:.0f} of {len(results)} winning attacks")
    for res in report.results:
        if res.scores.get("blocks_injection") != 1.0:
            err = (res.error or "").strip().splitlines()
            print(f"  not blocked: {scored[res.index]['id']} ({scored[res.index]['kind']})"
                  + (f"  error: {err[-1]}" if err else ""))

if __name__ == "__main__":
    main()
