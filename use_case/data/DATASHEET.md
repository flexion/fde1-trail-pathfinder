# Datasheet

## What this data is

**Generated on:** 2026-10-18
**Generated from:** `schema.py`'s `Request`/`Response` contract plus the 5
hand-written goldens in `use_case/evals/golden.jsonl`, crossed with the axes
in `02_Open_Weights/challenge/axes.py` — not real records.
**Rows:** 35

**Counts:** 36 generated (0 unparseable) → 36 distinct after dedupe (100%) →
35 schema-valid. 0 dead axis combinations (every one of the 12
`training_availability` × `gap_count` points produced at least one valid row).

**Settings:** `dedupe_threshold=0.7` (the `helpers.sdg.generate()` default,
not overridden — see the open question in `decisions.md`). Temperature and
top-p were left at the provider's defaults; neither was explicitly set in
`generate_data.py`, which is itself worth deciding on deliberately rather
than leaving implicit.

## Variation axes

| Axis | Values | Why it covers real variation |
| --- | --- | --- |
| `training_availability` | approved training exists / training exists but not yet approved / no training available / multiple trainings match | Tests whether the system recommends correctly, flags an unapproved match as a draft, declines instead of inventing a training, and handles a tie — covers the mandatory decline case |
| `gap_count` | zero gaps / one to three gaps / four or more gaps | Zero gaps tests the empty-result case; four-or-more is the only value that forces the "rank and cap at 3" rule to actually choose and cut something, instead of showing everything it found |

## What it can validate

Prototyping data, not backtesting — outputs were model-generated, not
verified. Validates that the schema holds across all 12 axis combinations
and that the pipeline runs end-to-end. Does not validate Pathfinder's actual
gap logic; only `golden.jsonl` carries that claim.

## What it cannot validate

- This data cannot show whether a self-rating is honest. A person who rates
  themselves Expert on every skill produces a zero-gap profile regardless of
  their real skill level, and the system has no way to tell the two apart —
  catching that would require an interactive, conversational assessment, which
  this system does not have. The `gap_count: zero_gaps` case only tests that
  the system displays an empty result correctly, not that the zero gaps are real.
- This data cannot prove each situation was tested 3 times, because 4 of the
  35 profiles don't match the situation they were labeled as. For example,
  Profile 32 was supposed to be missing 1 to 3 skills. It's missing none.
  Also, Profiles 7 and 34 were supposed to have training available. Each also
  has a skill with no training.
- This data cannot show how often having no skill gaps happens for real
  members, because we made an equal number of profiles for every situation on
  purpose.
- This data cannot show whether the trainings Pathfinder suggests are real and
  currently available to members, because the AI model made up the training
  list.
- This data cannot prove that the suggestions in this data are correct,
  because the same AI model wrote both the profiles and the suggestions, and no
  person has reviewed the suggestions against a real skills assessment.

## What it must never be compared against

TrailSkills 1.0 self-assessment data — it's documented as unreliable, and
these self-ratings are invented, so neither is real ground truth. No real
ground truth exists yet; `golden.jsonl` is the only verified reference.

## Leakage check — outward (what left)

- [x] No real record was used as a seed.
- [x] No real entity names, IDs, or identifiers appear.
- [x] No distinctive internal formats that would identify the firm.
- [x] Rare categories were generated, not copied.

## Leakage check — inward (what the eval shares with the training data)

**Are the goldens disjoint from anything the system was, or will be, tuned on?**
No — overlap: 3 of the 5 goldens (the first 3 in `golden.jsonl`) were shown to
the model as few-shot examples in every generation call for
`synthetic_v1.jsonl` (see `GENERATION_PROMPT` in `helpers/sdg.py`). The
synthetic rows are textually distinct (max 0.487 similarity by the dedupe
measure, below), but generatively anchored on those 3 goldens' style and
structure. Any model fine-tuned on `synthetic_v1.jsonl` (Week 8) should not be
scored against those same 3 goldens as an independent holdout.

**Overlap between `golden.jsonl` and this file, by the dedupe measure:** 0 of
35 synthetic rows at or above the 0.7 threshold against any of the 5 goldens
(highest observed similarity: 0.487).
