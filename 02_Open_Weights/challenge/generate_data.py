"""Generate use_case/data/synthetic_v1.jsonl from the TC2 axes and goldens.

    uv run python generate_data.py

Axes -> generate -> dedupe -> schema-validate, via the packaged loop in
helpers/sdg.py. Prints the honest counts (SDGReport): generated, after
dedupe, schema-valid, and any axis combinations that produced nothing.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "01_Product_Engineering" / "challenge"))

from pydantic import ValidationError

from axes import AXES
from schema import REC_MAX, Category, Request, Response, SkillLevel

from helpers import nb, sdg

GOLDEN = ROOT / "use_case" / "evals" / "golden-gap.jsonl"  # TC1 gap goldens; golden.jsonl is AI-1/AI-2 since 2026-10-29
OUT = ROOT / "use_case" / "data" / "synthetic_v1.jsonl"

# schema.py's `category` and skill-level fields are closed enums, not free
# text. The packaged generation prompt only shows 3 example rows and never
# states that constraint, so the model invents plausible-sounding categories
# ("Habitat Restoration", "Data Collection") that don't exist in the real
# system -- every row then fails schema validation. Telling it the exact
# closed vocabulary up front fixes that.
#
# Likewise, REC_MAX caps next_steps at 3, but the model has no way to infer
# that from 3 shown examples that may never have a many-gap profile -- it
# writes one next_step per gap instead, which fails validation on exactly the
# `four_or_more_gaps` axis value this dataset most needs to cover.
sdg.GENERATION_PROMPT += f"""

The `category` field (on every skill, in `required_skills`, `self_ratings`,
and `skills_taught`) must be exactly one of: {", ".join(c.value for c in Category)}.
Do not invent any other category.
Every skill level field (`required_level`, `level`) must be exactly one of:
{", ".join(l.value for l in SkillLevel)}.
`next_steps` must have at most {REC_MAX} items, even when there are more than
{REC_MAX} close-or-missing skills -- rank them and keep only the top {REC_MAX}."""


def validate(row: dict) -> bool:
    """A generated row must match the same contract the goldens do."""
    try:
        Request.model_validate(row["input"])
        Response.model_validate(row["output"])
    except (KeyError, ValidationError):
        return False
    return True


def main() -> int:
    cfg = nb.bootstrap()
    seeds = [
        json.loads(line)
        for line in GOLDEN.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows, report = sdg.generate(cfg, seeds, AXES, per_combo=3, validate=validate)

    OUT.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )

    print(report)
    print(f"wrote {len(rows)} rows -> {OUT}")
    if report.leaks:
        print(f"⚠️ possible leaks, check these before committing anything: {report.leaks}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
