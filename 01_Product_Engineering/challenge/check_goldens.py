"""Check use_case/evals/golden.jsonl against the contract in schema.py.

    uv run python check_goldens.py

Checks shape and the rules the goldens promise, not whether `solve()` agrees
with them; that comparison is the Week 4 eval. Exits non-zero on any failure.
"""

import json
import sys
from pathlib import Path

from pydantic import ValidationError

from schema import REC_MAX, GapStatus, Request, Response

GOLDENS = Path(__file__).resolve().parents[2] / "use_case" / "evals" / "golden.jsonl"
STATUS_ORDER = {GapStatus.HAS: 0, GapStatus.CLOSE: 1, GapStatus.MISSING: 2}


def problems(row: dict) -> list[str]:
    try:
        request = Request.model_validate(row["input"])
        response = Response.model_validate(row["output"])
    except (KeyError, ValidationError) as exc:
        return [f"does not match schema.py: {exc}"]

    found = []
    ranks = [STATUS_ORDER[g.status] for g in response.gaps]
    if ranks != sorted(ranks):
        found.append("gaps are not ordered has -> close -> missing")
    if len(response.next_steps) > REC_MAX:
        found.append(f"{len(response.next_steps)} next steps, more than REC_MAX ({REC_MAX})")
    catalog = {t.title for t in request.trainings}
    for step in response.next_steps:
        if step.training_title not in catalog:
            found.append(f"next step names '{step.training_title}', which is not in the request's catalog")
        # Same rule pathfinder applies to model-written reasons.
        if step.for_skill.skill.lower() not in step.reason.lower():
            found.append(f"reason for '{step.training_title}' does not name {step.for_skill.skill}")
    if response.needs_review and (response.gaps or response.next_steps):
        found.append("needs_review is true but gaps or next steps are filled in")
    return found


def main() -> int:
    failed = 0
    for n, line in enumerate(GOLDENS.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        found = problems(json.loads(line))
        print(f"row {n}: {'ok' if not found else 'FAIL'}")
        for problem in found:
            print(f"  - {problem}")
        failed += bool(found)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
