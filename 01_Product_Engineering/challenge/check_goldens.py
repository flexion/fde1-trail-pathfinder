"""Check the goldens in use_case/evals against the contracts in schema.py.

    uv run python check_goldens.py

Two files, two contracts:

- `golden.jsonl` (2026-10-29 pivot): AI-1 rows (`ExperienceRequest` →
  `CompetencySuggestions`) and AI-2 rows (`JobTextRequest` → `RoleMatches`).
  Every competency id, level and role id is checked against
  `data/framework.json`, which is built from the golden role profiles and
  mapping in the career-explorer repo. A reason that quotes the person must
  quote words that are actually in the text.
- `golden-gap.jsonl` (TC1): the gap-and-next-step rows, checked as before.

Checks shape and the rules the goldens promise, not whether the app agrees
with them; that comparison is the Week 4 eval. Exits non-zero on any failure.
"""

import json
import re
import sys
from pathlib import Path

from pydantic import ValidationError

from schema import (REC_MAX, CompetencySuggestions, Confidence, ExperienceRequest, GapStatus, JobTextRequest,
                    Request, Response, RoleMatches, SkillLevel)

EVALS = Path(__file__).resolve().parents[2] / "use_case" / "evals"
GOLDENS = EVALS / "golden.jsonl"
GAP_GOLDENS = EVALS / "golden-gap.jsonl"
FRAMEWORK = Path(__file__).resolve().parent / "data" / "framework.json"
STATUS_ORDER = {GapStatus.HAS: 0, GapStatus.CLOSE: 1, GapStatus.MISSING: 2}
MAX_ROLES = 3


def gap_problems(row: dict) -> list[str]:
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


def pivot_problems(row: dict, fw: dict) -> list[str]:
    competencies = {c["id"]: c for c in fw["competencies"]}
    roles = {r["id"]: r for r in fw["roles"]}
    backgrounds = {b["id"]: b for b in fw["backgrounds"]}
    found = []
    capability = row.get("capability")
    for key in ("id", "why", "status"):
        if not row.get(key):
            found.append(f"missing '{key}'")

    if capability == "AI-1":
        try:
            request = ExperienceRequest.model_validate(row["input"])
            output = CompetencySuggestions.model_validate(row["output"])
        except (KeyError, ValidationError) as exc:
            return [f"does not match schema.py: {exc}"]
        for b in request.backgrounds:
            if b not in backgrounds:
                found.append(f"background '{b}' is not in framework.json")
        if not request.backgrounds and not request.text.strip():
            found.append("empty input: no background and no text")
        for rid in request.rejected:
            if rid not in competencies:
                found.append(f"rejected id '{rid}' is not in the framework")
            if any(sug.skill_id == rid for sug in output.suggestions):
                found.append(f"'{rid}' was rejected but is suggested again")
        if output.declined and output.suggestions:
            found.append("declined but suggestions are filled in")
        if not output.declined and not output.suggestions:
            found.append("not declined but no suggestions")
        if output.declined and not output.reason:
            found.append("declined without a reason")
        if not output.declined and not output.sources:
            found.append("answered without sources")
        if not output.declined and not output.framework_version:
            found.append("answered without a framework_version")
        seen = set()
        text = request.text.casefold()
        # "I'm no expert" must not pass as her saying expert.
        said_expert = bool(re.search(r"\bexpert\b", text)) and not re.search(r"\b(no|not an?|never an?|hardly an?)\s+expert", text)
        for sug in output.suggestions:
            comp = competencies.get(sug.skill_id)
            if comp is None:
                found.append(f"competency id '{sug.skill_id}' is not in the framework")
                continue
            if comp["name"] != sug.skill or comp["category"] != sug.category:
                found.append(f"'{sug.skill_id}' is {comp['category']} / {comp['name']}, not {sug.category} / {sug.skill}")
            if sug.skill_id in seen:
                found.append(f"'{sug.skill_id}' suggested twice")
            seen.add(sug.skill_id)
            # A reason either quotes her words or names a background she picked.
            quoted = re.findall(r'"([^"]+)"', sug.reason)
            if sug.quote and sug.quote.casefold() not in text:
                found.append(f"'{sug.skill_id}' quote \"{sug.quote}\" is not in the text")
            if quoted and not sug.quote:
                found.append(f"reason for '{sug.skill_id}' quotes the text but `quote` is empty")
            if quoted:
                for q in quoted:
                    if q.casefold() not in text:
                        found.append(f"reason for '{sug.skill_id}' quotes \"{q}\", which is not in the text")
            else:
                label_hit = any(backgrounds[b]["label"].casefold() in sug.reason.casefold() for b in request.backgrounds)
                if not label_hit:
                    found.append(f"reason for '{sug.skill_id}' neither quotes the text nor names a picked background")
            # Expert is never the model's idea (team convention, evals/README.md).
            if sug.level == SkillLevel.EXPERT and not said_expert:
                found.append(f"'{sug.skill_id}' is Expert but she never said expert")
            if sug.confidence == Confidence.LIKELY and not quoted and sug.skill_id not in {
                x["skill_id"] for b in request.backgrounds for x in backgrounds[b]["suggestions"]
            }:
                found.append(f"'{sug.skill_id}' is likely with no quote and no background rule behind it")

    elif capability == "AI-2":
        try:
            JobTextRequest.model_validate(row["input"])
            output = RoleMatches.model_validate(row["output"])
        except (KeyError, ValidationError) as exc:
            return [f"does not match schema.py: {exc}"]
        if output.declined and output.roles:
            found.append("declined but roles are filled in")
        if not output.declined and not (1 <= len(output.roles) <= MAX_ROLES):
            found.append(f"{len(output.roles)} roles; AI-2 returns one to {MAX_ROLES}")
        if output.declined and not output.reason:
            found.append("declined without a reason")
        if not output.declined and not output.sources:
            found.append("answered without sources")
        if not output.declined and not output.framework_version:
            found.append("answered without a framework_version")
        for match in output.roles:
            role = roles.get(match.role_id)
            if role is None:
                found.append(f"role id '{match.role_id}' is not in the library")
            elif role["title"] != match.title:
                found.append(f"'{match.role_id}' is titled '{role['title']}', not '{match.title}'")
        listed = {m.role_id for m in output.roles}
        for role_id in row.get("also_acceptable", []):
            if role_id not in roles:
                found.append(f"also_acceptable '{role_id}' is not in the library")
            if role_id in listed:
                found.append(f"also_acceptable '{role_id}' is already in the answer")
    else:
        found.append(f"unknown capability '{capability}'")
    return found


def check(path: Path, problems) -> int:
    failed = 0
    print(path.name)
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        found = problems(row)
        print(f"  {row.get('id', f'row {n}')}: {'ok' if not found else 'FAIL'}")
        for problem in found:
            print(f"    - {problem}")
        failed += bool(found)
    return failed


def main() -> int:
    fw = json.loads(FRAMEWORK.read_text(encoding="utf-8"))
    failed = check(GOLDENS, lambda row: pivot_problems(row, fw))
    if GAP_GOLDENS.exists():
        failed += check(GAP_GOLDENS, gap_problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
