"""Week 4 Step 4: generate the failures the traces do not have, and see what catches them.

    uv run python use_case/evals/make_synthetic.py          # write synthetic.jsonl, score it -> synthetic_results.md

Start from outputs known to be correct (the AI-1 goldens, and the oracle's answer for
the three generated decline cases), break each in a named way, and label it with what
was broken: the label is free because we know what we did. Most modes come in an easy
and a hard version; the gap between the two is how much the easy ones flatter a scorer.

Every scorer from Step 2 and the Step 3 judge run over every broken output, and over the
unbroken originals as a false-alarm check.
"""

from __future__ import annotations

import copy
import json
import re
import sys
from pathlib import Path

from dotenv import load_dotenv

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from harness import SCORERS, framework, load_cases, make_judge, make_oracle  # noqa: E402

OUT = HERE / "synthetic.jsonl"
RESULTS = HERE / "synthetic_results.md"

# Failure mode -> the failures.md line (or guard) it exercises, and how often the fifty
# real traces showed it (from failures.md and the Step 2 scorers).
MODES = {
    "unrelated_chip_skill": ("line 5: a pre-checked chip skill her words do not relate to", 6),
    "wrong_skill_for_quote": ("line 6: names a skill her words do not describe", 5),
    "whole_sentence_quote": ("line 3: quote is a whole sentence of more than eight words", 9),
    "rules_label_with_text": ("line 4: she wrote text, the answer says the rules produced it", 8),
    "decline_asks_for_picked_background": ("line 10: a decline asks for a background she picked", 3),
    "invented_quote": ("guard: every quote is verbatim", 0),
    "unknown_skill_id": ("guard: every id is a real framework id", 0),
    "level_raised_without_basis": ("guard: nothing above Entry without a cited line", 0),
    "declines_when_she_said_enough": ("guard: declines only when it should", 0),
    "answers_when_it_should_decline": ("guard: declines when it should", 0),
}

# Same-category neighbours, for the hard version of a wrong skill: plausible, but not
# what she described.
NEIGHBOUR = {
    "Trail Construction": "decommissioning-trails",
    "Trail Maintenance": "maintenance-specifications",
    "Crew Management": "performance-management",
    "Program Administration": "policy-directives-law",
    "Project Planning and Design": "cost-estimation",
}


def comp(skill_id: str) -> dict:
    return next(c for c in framework()["competencies"] if c["id"] == skill_id)


def suggestion(skill_id: str, confidence: str, reason: str, quote: str | None = None) -> dict:
    c = comp(skill_id)
    return {"skill_id": skill_id, "category": c["category"], "skill": c["name"], "level": "Entry",
            "confidence": confidence, "reason": reason, "quote": quote, "level_basis": None}


def chip_label(case: dict) -> str | None:
    labels = {b["id"]: b["label"] for b in framework()["backgrounds"]}
    picked = [b for b in case["input"].get("backgrounds", []) if b != "none"]
    return labels[picked[0]].lower() if picked else None


def quoted(out: dict) -> list[dict]:
    return [s for s in out.get("suggestions", []) if s.get("quote")]


# --- the breaks: each takes a case and its correct output, returns (corrupted, note) or None ---


def unrelated_chip_skill(case, out, hard):
    """A pre-checked skill from her chip that nothing she wrote relates to. Under the easy
    rule a trail skill for someone who did trail work is plausible (transferable), so the
    added skill is from a different area entirely: office and planning work for people
    who wrote about field work. (A first version added Decommissioning Trails or a
    chainsaw skill to trail builders; the judge rightly passed those as transferable.)"""
    label = chip_label(case)
    if not label or not case["input"].get("text", "").strip():
        return None
    o = copy.deepcopy(out)
    sid, conf = ("cost-estimation", "possible") if hard else ("contract-administration", "likely")
    if any(s["skill_id"] == sid for s in o["suggestions"]):
        return None
    o["suggestions"].append(suggestion(sid, conf, f"Common for people with {label} experience"))
    return o, f"added {sid} as {conf} under her chip"


def wrong_skill_for_quote(case, out, hard):
    qs = quoted(out)
    if not qs:
        return None
    o = copy.deepcopy(out)
    target = next(s for s in o["suggestions"] if s.get("quote"))
    new = NEIGHBOUR[target["category"]] if hard else "budgeting"
    if any(s["skill_id"] == new for s in o["suggestions"]):
        return None
    c = comp(new)
    note = f"'{target['quote']}' now points to {new} instead of {target['skill_id']}"
    target.update(skill_id=new, skill=c["name"], category=c["category"], level="Entry", level_basis=None)
    return o, note


def whole_sentence_quote(case, out, hard):
    text = case["input"].get("text", "")
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    o = copy.deepcopy(out)
    for s in o["suggestions"]:
        if not s.get("quote"):
            continue
        whole = next((x for x in sentences if s["quote"].casefold() in x.casefold()), None)
        if whole and len(whole.split()) > 8 and whole.casefold() != s["quote"].casefold():
            s["quote"], s["reason"] = whole, f'You wrote "{whole}"'
            return o, "quote widened to its whole sentence"
    return None


def rules_label_with_text(case, out, hard):
    if not case["input"].get("text", "").strip() or out.get("declined"):
        return None
    o = copy.deepcopy(out)
    o["produced_by"] = "rules"
    return o, "produced_by set to rules"


def decline_asks_for_picked_background(case, out, hard):
    if not out.get("declined") or not case["input"].get("backgrounds"):
        return None
    o = copy.deepcopy(out)
    o["reason"] = ("Nothing here maps to a trail competency. Pick a background or describe any outdoor, "
                   "construction or crew work.")
    return o, "decline reason asks her to pick a background"


def invented_quote(case, out, hard):
    o = copy.deepcopy(out)
    for s in o["suggestions"]:
        if s.get("quote"):
            words = s["quote"].split()
            q = " ".join([words[0], "carefully", *words[1:]]) if hard else "twenty years of professional experience"
            s["quote"], s["reason"] = q, f'You wrote "{q}"'
            return o, f"quote changed to '{q}'"
    return None


def unknown_skill_id(case, out, hard):
    if not out.get("suggestions"):
        return None
    o = copy.deepcopy(out)
    s = o["suggestions"][0]
    s["skill_id"] = f"{s['skill_id']}-3" if hard else "chainsaw-expert"
    return o, f"id changed to {s['skill_id']}"


def level_raised_without_basis(case, out, hard):
    o = copy.deepcopy(out)
    for s in o["suggestions"]:
        if s.get("quote") and s["level"] == "Entry":
            s["level"], s["level_basis"] = ("Expert" if hard else "Full Performance"), None
            return o, f"{s['skill_id']} raised to {s['level']} with no level_basis"
    return None


def declines_when_she_said_enough(case, out, hard):
    if out.get("declined") or not quoted(out):
        return None
    return ({"declined": True, "suggestions": [], "sources": [], "produced_by": "model",
             "reason": "Not enough to go on: no task, tool or feature is named. Ask for what the work involved."},
            "declined an input with quotable work")


def answers_when_it_should_decline(case, out, hard):
    if not out.get("declined"):
        return None
    text = case["input"].get("text", "")
    if hard and text:   # a quote of hers, a believable stretch: "worked on trails", "assistant manager"
        words = text.rstrip(".").split()
        quote = " ".join(words[-3:])
        s = suggestion("crew-management", "possible", f'You wrote "{quote}"', quote)
    else:
        s = suggestion("hand-built-trail-construction", "likely", "Common for people with trail volunteering experience")
    return ({"declined": False, "suggestions": [s], "sources": [f"framework:competency:{s['skill_id']}"],
             "framework_version": "synthetic", "produced_by": "model", "reason": None}, "answered instead of declining")


BREAKS = {name: globals()[name] for name in MODES}


def build() -> list[dict]:
    cases = load_cases()
    oracle = make_oracle(cases)
    base = [c for c in cases if not c["id"].startswith("t-gen-") or c["output"].get("declined")]
    rows = []
    for mode, fn in BREAKS.items():
        for hard in (False, True):
            for case in base:
                original = json.loads(oracle(case["input"]))
                made = fn(case, original, hard)
                if made is None:
                    continue
                corrupted, note = made
                if corrupted == original:
                    continue
                rows.append({"id": f"syn-{mode}-{'hard' if hard else 'easy'}-{case['id']}", "mode": mode,
                             "hard": hard, "case": case["id"], "input": case["input"],
                             "original": original, "corrupted": corrupted, "note": note})
    # A mode whose hard version is the same break as the easy one keeps only the easy rows.
    seen, out = set(), []
    for r in rows:
        k = (r["mode"], r["case"], json.dumps(r["corrupted"], sort_keys=True))
        if k not in seen:
            seen.add(k)
            out.append(r)
    return out


def main() -> None:
    load_dotenv(ROOT / ".env", override=True)
    import litellm

    litellm.suppress_debug_info = True
    from helpers import config
    from helpers.judge import Calibration
    from helpers.llm import CallStats

    rows = build()
    stats = CallStats()
    judge = make_judge(config.from_env(ROOT), stats=stats)
    judge.calibration = Calibration(passed=True)   # passed in check_judge.py; see judge_results.md

    cases = {c["id"]: c for c in load_cases()}
    for r in rows:
        expect = cases[r["case"]]["output"]
        # declines_when_it_should needs the case's own expectation, not the default above.
        a, case = json.dumps(r["corrupted"]), {"input": r["input"], "output": expect}
        r["caught"] = {name: f(a, case) < 1.0 for name, f in SCORERS.items()}
        r["caught"]["judge"] = judge._raw_score(a, {"input": json.dumps(r["input"])}) < 0.5
    originals = {}
    for r in rows:
        if r["case"] not in originals:
            o = r["original"]
            a, case = json.dumps(o), {"input": r["input"], "output": cases[r["case"]]["output"]}
            got = {name: f(a, case) < 1.0 for name, f in SCORERS.items()}
            got["judge"] = judge._raw_score(a, {"input": json.dumps(r["input"])}) < 0.5
            originals[r["case"]] = got
    OUT.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    cols = [*SCORERS, "judge"]
    natural_total = sum(n for _, n in MODES.values())
    lines = [
        "# Synthetic failures (Week 4 Step 4)",
        "",
        f"**Natural vs generated.** The fifty traces showed {natural_total} failures across these modes "
        f"(counted per trace, from failures.md; five of the ten modes never happened). "
        f"Generated here: **{len(rows)}** broken outputs from {len(originals)} correct ones "
        "(the 13 AI-1 goldens and the oracle's answer for the three generated decline cases).",
        "",
        "Each cell: the share of that mode's broken outputs the scorer caught (scored it below 1).",
        "",
        "| mode | exercises | natural | generated | " + " | ".join(cols) + " |",
        "| --- | --- | --- | --- | " + " | ".join("---" for _ in cols) + " |",
    ]
    for mode, (what, natural) in MODES.items():
        for hard in (False, True):
            rs = [r for r in rows if r["mode"] == mode and r["hard"] == hard]
            if not rs:
                continue
            cells = " | ".join(f"{sum(r['caught'][c] for r in rs) / len(rs):.2f}" for c in cols)
            lines.append(f"| {mode} ({'hard' if hard else 'easy'}) | {what} | {natural if not hard else ''} | {len(rs)} | {cells} |")
    fa = " | ".join(f"{sum(o[c] for o in originals.values()) / len(originals):.2f}" for c in cols)
    lines += [f"| *unbroken originals (false alarms)* | | | {len(originals)} | {fa} |", "",
              f"Judge calls: {stats.calls}, {stats.prompt_tokens + stats.completion_tokens:,} tokens, {stats.seconds:.0f} s (measured)."]
    RESULTS.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
