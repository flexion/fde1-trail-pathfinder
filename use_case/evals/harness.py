"""Week 4: the AI-1 eval harness. Cases, systems and model-free scorers.

`helpers.harness` does the plumbing (run, save, load, compare). This file says
what "correct" means for `suggest_competencies`. Every scorer names the line of
`failures.md` it catches; each is `(actual, case) -> 0..1`, and an output that
does not parse scores 0, never 1.

Cases are the fifty trace inputs (`trace_inputs.jsonl`). A case's `output` is
the golden output for the 13 golden inputs. The 37 generated inputs have no
golden, so their `output` holds only whether a decline is expected.

Not scored by code, decided 2026-11-02:
    line 1  a `likely` skill with nothing she wrote behind it. The goldens keep the
            prototype's chip confidence, so a code scorer would fail the oracle.
    line 2  duplicate twins. Both are real skills; the goldens list both on purpose.
"""

from __future__ import annotations

import json
import re
import sys
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_Product_Engineering" / "challenge"
EVALS = ROOT / "use_case" / "evals"
sys.path.insert(0, str(APP))

# The generated inputs that should decline: no background picked and no trail,
# outdoor or crew work named (gen-30, gen-31), or the "No trail experience yet"
# chip with no text (gen-37). Every other generated input has a chip or a task.
EXPECT_DECLINE = {"t-gen-30", "t-gen-31", "t-gen-37"}


@cache
def framework() -> dict:
    return json.loads((APP / "data" / "framework.json").read_text(encoding="utf-8"))


def load_cases() -> list[dict]:
    goldens = {}
    for line in (EVALS / "golden.jsonl").read_text(encoding="utf-8").splitlines():
        g = json.loads(line)
        goldens[g["id"]] = g
    cases = []
    for line in (EVALS / "trace_inputs.jsonl").read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row["source"] == "golden":
            output = goldens[row["golden"]]["output"]
        else:
            output = {"declined": row["id"] in EXPECT_DECLINE}
        cases.append({"id": row["id"], "input": row["input"], "output": output})
    return cases


def parse(actual: str):
    """The endpoint's JSON as a CompetencySuggestions, or None. Every field of the model has
    a default, so `declined` and `suggestions` must be present: without that check the echo
    baseline (her input, as JSON) parsed as an empty answer and scored 1.0."""
    from pydantic import ValidationError

    from schema import CompetencySuggestions

    try:
        raw = json.loads(actual)
        if not isinstance(raw, dict) or not {"declined", "suggestions"} <= raw.keys():
            return None
        return CompetencySuggestions.model_validate(raw)
    except (ValidationError, ValueError):
        return None


# --- scorers ---------------------------------------------------------------------------


def valid_output(actual: str, case: dict) -> float:
    """Guards failures.md "What went right": ids real, quotes verbatim, rejected ids never
    re-offered, nothing above Entry without a cited line, a decline carries no suggestions.
    True of all fifty traces; this is the regression check that keeps it true."""
    out = parse(actual)
    if out is None:
        return 0.0
    comps = {c["id"]: c for c in framework()["competencies"]}
    text = case["input"].get("text", "").casefold()
    rejected = set(case["input"].get("rejected", []))
    if out.declined and out.suggestions:
        return 0.0
    for s in out.suggestions:
        comp = comps.get(s.skill_id)
        if comp is None or comp["name"] != s.skill or comp["category"] != s.category:
            return 0.0
        if s.quote and s.quote.casefold() not in text:
            return 0.0
        if s.skill_id in rejected:
            return 0.0
        if s.level != "Entry" and not (s.quote and s.level_basis):
            return 0.0
    return 1.0


def declines_when_it_should(actual: str, case: dict) -> float:
    """failures.md "What went right": it declines exactly when it should, and answers otherwise."""
    out = parse(actual)
    if out is None:
        return 0.0
    return 1.0 if out.declined == bool(case["output"].get("declined")) else 0.0


def decline_wording(actual: str, case: dict) -> float:
    """failures.md line 10: a decline never asks for a background she already picked
    ("No trail experience yet" is one). An answer that is not a decline passes."""
    out = parse(actual)
    if out is None:
        return 0.0
    if out.declined and case["input"].get("backgrounds") and "pick a background" in (out.reason or "").lower():
        return 0.0
    return 1.0


def quote_is_a_phrase(actual: str, case: dict) -> float:
    """failures.md line 3: a quote should point at the words that matter, not repeat a
    whole sentence of hers. Fails when a quote is an entire sentence of more than eight
    words. Eight, not fewer: golden ai1-05 quotes "Expert at dry-stone retaining walls and
    rock steps", a whole eight-word sentence about one skill, and that is a good quote."""
    out = parse(actual)
    if out is None:
        return 0.0
    sentences = {re.sub(r"\W+$", "", s.strip()).casefold()
                 for s in re.split(r"(?<=[.!?])\s+", case["input"].get("text", "")) if s.strip()}
    for s in out.suggestions:
        if not s.quote:
            continue
        quote = re.sub(r"\W+$", "", s.quote.strip()).casefold()
        if quote in sentences and len(quote.split()) > 8:
            return 0.0
    return 1.0


def labelled_by_source(actual: str, case: dict) -> float:
    """failures.md line 4: when she wrote text, the answer must not say the rules produced
    it. Either the model ran and found nothing (mislabelled) or the model path failed and
    fell back; both are worth counting."""
    out = parse(actual)
    if out is None:
        return 0.0
    has_text = bool(case["input"].get("text", "").strip())
    return 0.0 if has_text and out.produced_by == "rules" else 1.0


SCORERS = {
    "valid_output": valid_output,
    "declines_when_it_should": declines_when_it_should,
    "decline_wording": decline_wording,
    "quote_is_a_phrase": quote_is_a_phrase,
    "labelled_by_source": labelled_by_source,
}


# --- systems ---------------------------------------------------------------------------
# helpers.harness calls system(case["input"]) and scores the string it returns.


def key(case_input: dict) -> str:
    return json.dumps(case_input, sort_keys=True)


def echo(case_input: dict) -> str:
    """Dumb baseline: returns the input. Anything that does not beat this is broken."""
    return json.dumps(case_input)


def make_oracle(cases: list[dict]):
    """Returns the golden output. For a generated input, which has no golden, the minimal
    correct answer: a decline when one is expected, otherwise no suggestions. So on those
    the oracle checks the scorers' own logic, not skill choice."""
    answers = {}
    for case in cases:
        out = dict(case["output"])
        if "suggestions" not in out:
            out = {"declined": out["declined"], "suggestions": [],
                   "reason": "Not enough to go on." if out["declined"] else None,
                   "produced_by": "model" if case["input"].get("text") else "rules"}
        answers[key(case["input"])] = json.dumps(out)
    return lambda case_input: answers[key(case_input)]


def endpoint(case_input: dict) -> str:
    """The system under test: suggest_competencies, in-process (the same code as the API)."""
    from schema import ExperienceRequest
    from suggest import suggest

    return suggest(ExperienceRequest.model_validate(case_input)).model_dump_json()


def make_replay(path: Path):
    """The recorded traces as a system, for working on scorers without model calls."""
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    answers = {key(r["input"]): json.dumps(r["output"]) for r in rows}
    return lambda case_input: answers[key(case_input)]
