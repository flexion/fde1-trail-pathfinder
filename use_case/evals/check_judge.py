"""Week 4 Step 3: check the judge before trusting it. Both halves.

    uv run python use_case/evals/check_judge.py

Separation: on the 13 AI-1 goldens, the judge scores the golden output (known good),
a well-formed answer of unrelated pre-checked skills (KNOWN_BAD) and the echo of her
input (known bad). `helpers.judge` passes it when good > 0.8 and bad < 0.3.

Agreement: on the twenty hand scores (`human_scores.jsonl`), how often the judge's
pass/fail matches the human's, against the chance floor (always guessing the more
common verdict). The judge covers failures.md lines 5 and 6, not decline wording
(line 10, a code scorer), so agreement is reported two ways: the judge alone, and the
judge together with `decline_wording`, which is how a trace is finally scored.

Writes judge_results.md and judge_results.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from harness import JUDGE_MODEL, KNOWN_BAD, decline_wording, echo, load_cases, make_judge  # noqa: E402


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)
    import litellm

    litellm.suppress_debug_info = True
    from helpers import config
    from helpers.llm import CallStats

    cfg = config.from_env(ROOT)
    stats = CallStats()
    judge = make_judge(cfg, stats=stats)

    # Separation, on the goldens: the judge sees her input and an answer, as JSON.
    goldens = [c for c in load_cases() if not c["id"].startswith("t-gen-")]
    as_text = [{"input": json.dumps(c["input"]), "output": json.dumps(c["output"]), "id": c["id"]} for c in goldens]
    cal = judge.calibrate(as_text, wrong_answer=KNOWN_BAD)
    echo_scores = [judge._raw_score(echo(c["input"]), {"input": json.dumps(c["input"])}) for c in goldens]
    echo_mean = sum(echo_scores) / len(echo_scores)

    # Agreement, on the twenty hand scores.
    rows = [json.loads(line) for line in (HERE / "human_scores.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    detail = []
    for r in rows:
        actual = json.dumps(r["actual"])
        case = {"input": r["input"]}
        j = judge._raw_score(actual, {"input": json.dumps(r["input"])}) >= 0.5
        combined = j and decline_wording(actual, case) == 1.0
        detail.append({"id": r["id"], "human": r["pass"], "judge": j, "combined": combined})
    n = len(detail)
    human_pass = sum(d["human"] for d in detail)
    floor = max(human_pass, n - human_pass) / n
    agree_judge = sum(d["judge"] == d["human"] for d in detail) / n
    agree_combined = sum(d["combined"] == d["human"] for d in detail) / n

    lines = [
        "# Judge check (Week 4 Step 3)",
        "",
        f"Judge model: `{JUDGE_MODEL}` (the endpoint answers with `{cfg.llm_model}`). "
        "Rubric: `JUDGE_RUBRIC` in `harness.py`, for failures.md lines 5 and 6 under the easy rule.",
        "",
        "## Separation (13 AI-1 goldens)",
        "",
        "| answer | judge mean |",
        "| --- | --- |",
        f"| golden output (known good) | {cal.accepted:.2f} |",
        f"| unrelated pre-checked skills (known bad) | {cal.wrong:.2f} |",
        f"| echo of her input (known bad) | {echo_mean:.2f} |",
        "",
        f"`helpers.judge`: **{cal}**",
        "",
        "## Agreement (20 hand scores)",
        "",
        f"Human: {human_pass} pass, {n - human_pass} fail. Chance floor (always guess the more common verdict): {floor:.2f}.",
        "",
        "| | agreement |",
        "| --- | --- |",
        f"| judge alone | {agree_judge:.2f} |",
        f"| judge + `decline_wording` (how a trace is scored) | {agree_combined:.2f} |",
        "",
        "| id | human | judge | judge + decline_wording |",
        "| --- | --- | --- | --- |",
    ]
    mark = {True: "pass", False: "fail"}
    for d in detail:
        flag = "" if d["combined"] == d["human"] else " ⚠️"
        lines.append(f"| {d['id']} | {mark[d['human']]} | {mark[d['judge']]} | {mark[d['combined']]}{flag} |")
    lines += ["", f"Judge calls: {stats.calls}, {stats.prompt_tokens:,} prompt + {stats.completion_tokens:,} completion tokens, "
              f"{stats.seconds:.0f} s (measured)."]
    (HERE / "judge_results.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (HERE / "judge_results.json").write_text(json.dumps({
        "model": JUDGE_MODEL, "separation": {"good": cal.accepted, "known_bad": cal.wrong, "echo": echo_mean,
                                             "passed": cal.passed, "detail": cal.detail},
        "agreement": {"judge": agree_judge, "combined": agree_combined, "floor": floor, "detail": detail},
        "calls": stats.calls}, indent=2) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
