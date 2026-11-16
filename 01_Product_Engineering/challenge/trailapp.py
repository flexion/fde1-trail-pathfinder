"""The TrailSkills prototype's side of AI-1: its ids in, its field names out.

The career-explorer prototype (flexion/flexion-trailskills2.0-career-explorer, v3)
calls `POST /api/suggest` in place of its own `translate()` and keeps `translate()`
as the fallback. It speaks its own vocabulary, so this module translates at the edge
and `suggest.py` stays unchanged:

- Work-type chips. v3 merged our backgrounds into broader chips. Each maps to the
  backgrounds it was merged from, in the order that reproduces v3's own scores (the
  first background wins where two suggest the same skill). Ten of v3's 14 chips
  suggest nothing in the prototype either, so they map to nothing here.
- Competency ids. `build_corpus.py` renames one id (RENAME_SKILL); it goes back to the
  prototype's spelling on the way out, and comes in that spelling in `rejected`.
- Levels and field names: `entry`/`full`/`expert`, and `skillId`, `conf`, `why`, `keep`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from schema import CompetencySuggestions, Confidence, ExperienceRequest, SkillLevel

# v3 chip id -> our background ids, first one wins on a shared skill.
BACKGROUNDS = {
    "trail-volunteering-corps": ["volunteer", "corps"],
    "construction-landscaping": ["construction", "landscape"],
    "forestry": ["forestry"],
    "military": ["military"],
}
# The prototype's id -> ours. The inverse of build_corpus.RENAME_SKILL's effect.
SKILL_IN = {"drainage-features-water-management": "water-management-drainage-features-2"}
SKILL_OUT = {ours: theirs for theirs, ours in SKILL_IN.items()}
LEVEL_OUT = {SkillLevel.ENTRY: "entry", SkillLevel.FULL_PERFORMANCE: "full", SkillLevel.EXPERT: "expert"}


class PrototypeRequest(BaseModel):
    """What the prototype's Your Experience page sends."""

    text: str = Field(default="", max_length=4000)
    backgrounds: list[str] = Field(default_factory=list, max_length=20)
    rejected: list[str] = Field(default_factory=list, max_length=60)


def to_request(body: PrototypeRequest) -> ExperienceRequest:
    backgrounds: list[str] = []
    for chip in body.backgrounds:
        for ours in BACKGROUNDS.get(chip, []):
            if ours not in backgrounds:
                backgrounds.append(ours)
    return ExperienceRequest(
        text=body.text,
        backgrounds=backgrounds,
        rejected=[SKILL_IN.get(s, s) for s in body.rejected],
    )


def to_prototype(result: CompetencySuggestions) -> dict:
    return {
        "suggestions": [
            {
                "skillId": SKILL_OUT.get(s.skill_id, s.skill_id),
                "level": LEVEL_OUT[s.level],
                "conf": s.confidence.value,
                "why": s.reason,
                # Likely and possible are pre-checked; check is not. She confirms every one.
                "keep": s.confidence != Confidence.CHECK,
            }
            for s in result.suggestions
        ],
        "declined": result.declined,
        "reason": result.reason,
        "followUp": result.follow_up_prompt,
        "producedBy": result.produced_by,
        "frameworkVersion": result.framework_version,
    }
