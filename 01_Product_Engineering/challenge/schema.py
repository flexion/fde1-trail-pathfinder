"""The contract for Trail Pathfinder: gap and next step.

Written in TC1 Step 5, before any implementation. The charter's In → Out row
is the prose version of this file; `use_case/CHARTER.md` is the source.

Week 1 passed the role's required skills and the training catalog slice in
with the request, because nothing could retrieve them yet. Week 3 (TC3) makes
both optional: left empty, the app looks them up in its stored corpus
(`corpus.py`) by role name within a scope, and `Response.sources` names the
record ids it used. The shape of the answer otherwise does not change.

TC3 also adds `Answer`: the contract for `ask_pathfinder`, a free-text
question answered from the same records, with sources, that can decline.

2026-10-28 pivot (product owner meeting, see use_case/stakeholders.md): the
product's P1 AI features are AI-1 and AI-2 of the career-explorer repo's
`docs/trailskills-2.0/04-ai-integration-spec.md`. `ExperienceRequest` →
`CompetencySuggestions` is AI-1; `JobTextRequest` → `RoleMatches` is AI-2.
The gap contract above stays as the downstream step (AI-4).
"""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

# At most this many next steps, ranked. A business rule (BR-6.5) with a
# configured value, never hard-coded in a function body.
REC_MAX = int(os.getenv("REC_MAX", "3"))


class Category(StrEnum):
    """The five framework categories. A skill is always scoped to one."""

    TRAIL_CONSTRUCTION = "Trail Construction"
    TRAIL_MAINTENANCE = "Trail Maintenance"
    PROJECT_PLANNING_AND_DESIGN = "Project Planning and Design"
    CREW_MANAGEMENT = "Crew Management"
    PROGRAM_ADMINISTRATION = "Program Administration"


class SkillLevel(StrEnum):
    """The three framework levels. Not an evidence tier."""

    ENTRY = "Entry"
    FULL_PERFORMANCE = "Full Performance"
    EXPERT = "Expert"


class GapStatus(StrEnum):
    HAS = "has"
    CLOSE = "close"  # exactly one level below what the role requires
    MISSING = "missing"  # two levels below, or no rating at all


class SkillRef(BaseModel):
    """A skill named with its category. Same name in two categories is two skills."""

    category: Category
    skill: str = Field(description="Exact framework skill name, as authored")


class RequiredSkill(SkillRef):
    required_level: SkillLevel


class SelfRating(SkillRef):
    level: SkillLevel | None = Field(
        default=None, description="None means she does not claim this skill yet"
    )


class Training(BaseModel):
    """One catalog offering, as the provider declares it. Never invented."""

    title: str
    skills_taught: list[RequiredSkill] = Field(
        description="Which skills and levels the provider says this builds"
    )
    cost_usd: float | None = Field(default=None, description="None means cost not stated")
    proves: str = Field(description="What completing it gives her: a card, a cert, hours")
    alignment_approved: bool = Field(
        default=False,
        description="True once a framework steward approved the skill alignment (BR-3.6)",
    )


class Request(BaseModel):
    """What the explorer hands in. The governed content (requirements, catalog)
    is looked up from the stored corpus unless the caller supplies it."""

    role: str = Field(description="A draft role from the role library, by name")
    self_ratings: list[SelfRating] = Field(
        description="Her rating on each required skill. Unrated skills count as missing."
    )
    scope: str = Field(
        default="trailskills",
        description="Which stored records to look in: 'trailskills' (the real role library) or a scenario id",
    )
    required_skills: list[RequiredSkill] = Field(
        default_factory=list,
        description="The role's required skills and levels. Empty means look the role up in the corpus.",
    )
    trainings: list[Training] = Field(
        default_factory=list,
        description="The catalog slice that touches these skills. Empty means look it up in the corpus.",
    )


class SkillGap(RequiredSkill):
    her_level: SkillLevel | None
    status: GapStatus


class NextStep(BaseModel):
    for_skill: SkillRef
    training_title: str = Field(description="Exactly as it appears in the catalog")
    cost_usd: float | None
    proves: str
    reason: str = Field(description="One line, naming the skill and the level gap it closes")


class Response(BaseModel):
    """What comes back. Strengths first, then gaps, then at most REC_MAX steps."""

    gaps: list[SkillGap] = Field(
        description="Every required skill, ordered has → close → missing"
    )
    next_steps: list[NextStep] = Field(
        default_factory=list, max_length=REC_MAX, description="Ranked. Empty is allowed."
    )
    no_training_for: list[SkillRef] = Field(
        default_factory=list,
        description="Close or missing skills with no catalog offering. Said, not papered over.",
    )
    summary: str = Field(description="One plain sentence she can read on a phone")
    needs_review: bool = Field(
        default=False,
        description=(
            "The no-answer flag. True when the input could not be scored (unknown skill, "
            "category mismatch) or the model output failed validation. Route to the manual "
            "path; do not show gaps or steps."
        ),
    )
    review_reason: str | None = Field(default=None, description="Why needs_review is True")
    sources: list[str] = Field(
        default_factory=list,
        description="Record ids the answer was grounded in: the role record and every training considered. Empty when the caller supplied the content itself.",
    )


class Answer(BaseModel):
    """What `ask_pathfinder` returns: a grounded answer to one question, or a decline."""

    question: str
    scope: str
    answer: str = Field(description="Plain text she can read on a phone. Names the records it used.")
    sources: list[str] = Field(
        default_factory=list, description="Every record id the answer was grounded in. Never empty unless declined."
    )
    declined: bool = Field(
        default=False,
        description="True when the stored records cannot answer: nothing in scope is named, or the fact asked for is not a field any record has.",
    )
    reason: str | None = Field(default=None, description="Why it declined, or why the model's words were replaced")
    trace: dict = Field(default_factory=dict, description="What the lookup matched: roles, trainings, skills")


class Confidence(StrEnum):
    """How sure a suggestion is. `likely` and `possible` are pre-checked on screen,
    `check` is not. The person confirms every one; nothing is recorded until then."""

    LIKELY = "likely"
    POSSIBLE = "possible"
    CHECK = "check"


class ExperienceRequest(BaseModel):
    """AI-1 input: what she has done, in her words, plus any backgrounds she picked."""

    backgrounds: list[str] = Field(
        default_factory=list,
        description="Background ids from data/framework.json (corps, military, landscape, ...). May be empty.",
    )
    text: str = Field(default="", description="Her own words. May be empty when a background is picked.")
    rejected: list[str] = Field(
        default_factory=list,
        description="Competency ids she rejected earlier in this session. Never re-offered (spec AI-1).",
    )


class CompetencySuggestion(BaseModel):
    """One proposed competency. Every id and level is checked against the framework
    before it reaches the screen; an unknown id is dropped, never shown (BR-10.5)."""

    skill_id: str = Field(description="Competency id from data/framework.json")
    category: Category
    skill: str = Field(description="Competency name, as the framework spells it")
    level: SkillLevel
    confidence: Confidence
    reason: str = Field(description="One line. Quotes her words, or names the background it came from.")
    quote: str | None = Field(
        default=None,
        description="The exact words of hers this rests on (spec §6, 'quoted source text'). None when it came from a background rule.",
    )


class CompetencySuggestions(BaseModel):
    """AI-1 output: at most 12 suggestions, or a decline when the text names nothing."""

    suggestions: list[CompetencySuggestion] = Field(default_factory=list, max_length=12)
    declined: bool = Field(default=False, description="True when nothing in the text or backgrounds maps to a competency")
    reason: str | None = Field(default=None, description="Why it declined")
    sources: list[str] = Field(default_factory=list, description="Framework and rule records the suggestions were grounded in")
    framework_version: str | None = Field(
        default=None, description="Which golden data answered, e.g. 'role profiles and competency map 2026-10-20' (spec §6)"
    )
    produced_by: Literal["rules", "model"] | None = Field(
        default=None, description="What the screen's AI label says: the rule-based fallback or the model. None in a golden."
    )


class JobTextRequest(BaseModel):
    """AI-2 input: a description of her current job, or a pasted posting."""

    text: str


class RoleMatch(BaseModel):
    role_id: str = Field(description="Role id from data/framework.json")
    title: str
    reason: str = Field(description="One line, drawn from the role profile")


class RoleMatches(BaseModel):
    """AI-2 output: the one to three closest of the 12 roles, or a decline when
    the library has nothing close ("The role library doesn't cover that yet")."""

    roles: list[RoleMatch] = Field(default_factory=list, max_length=3)
    declined: bool = False
    reason: str | None = None
    sources: list[str] = Field(default_factory=list)
    framework_version: str | None = None
    produced_by: Literal["rules", "model"] | None = None


def solve(request: Request, *, use_model: bool = True) -> Response:
    """The whole product as one signature.

    Compute the gap deterministically from ratings against requirements. Pick
    up to REC_MAX trainings whose declared skills close a close-or-missing
    gap. Write one-line reasons. Never assert a fact the request did not
    carry. Implemented in `pathfinder.solve()`; reimplemented over retrieval in TC3.
    """
    from pathfinder import solve as _solve

    return _solve(request, use_model=use_model)
