"""Build the app's stored corpus: the records the endpoint looks up and cites.

Run from the repository root:
    uv run python use_case/build_corpus.py [--explorer PATH]

Writes 01_Product_Engineering/challenge/data/corpus.jsonl, one record per line:

    {"id", "scope", "kind": "role" | "training", "title", "source": {...},
     "synthetic": bool, "fixture": bool, "data": {...}}

`scope` is the partition a lookup is confined to before anything is ranked:

    trailskills   the real role library from the Trail Skills Project partners
                  (12 roles, October 2026) plus the prototype's sample course
                  listings, read from the career-explorer repository
    golden-NN     the hand-written TC1 scenarios (use_case/evals/retrieval-corpus.jsonl)
    tc2-profile-* the TC2 synthetic scenarios (use_case/data/retrieval_sources.jsonl,
                  local only; skipped when absent)

Every record keeps its origin (repository, path, commit or checksum). A record
is never merged across scopes: two scopes can both hold a "Trail Crew Member"
and they are two different records on purpose (see TC3_DATA_REVIEW.md).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "01_Product_Engineering" / "challenge" / "data" / "corpus.jsonl"
FRAMEWORK_OUT = OUT.parent / "framework.json"
FIXTURES = ROOT / "use_case" / "evals" / "retrieval-corpus.jsonl"
TC2 = ROOT / "use_case" / "data" / "retrieval_sources.jsonl"
EXPLORER_DEFAULT = ROOT.parent / "flexion-trailskills2.0-career-explorer"

# The prototype's level ids -> the framework's level names (schema.SkillLevel).
LEVEL = {"entry": "Entry", "full": "Full Performance", "expert": "Expert"}
# The prototype's category ids -> the app's Category values. The prototype shows
# "Crew Leadership" for crew-management; the app's schema says "Crew Management",
# which is the trailskills.org URL slug and the name the goldens use.
CATEGORY = {
    "trail-construction": "Trail Construction",
    "trail-maintenance": "Trail Maintenance",
    "project-planning-and-design": "Project Planning and Design",
    "crew-management": "Crew Management",
    "program-administration": "Program Administration",
}


def git_head(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def js_object_literal(text: str) -> list:
    """Turn the prototype's `const COURSES = [...]` literal into JSON.

    The file is hand-written JS, not JSON: unquoted keys and trailing commas.
    Quoting keys and stripping trailing commas is all it takes here; if the
    prototype's style changes, this breaks loudly rather than silently.
    """
    start = text.index("const COURSES = [")
    end = text.index("];", start)
    literal = text[start + len("const COURSES = ") : end + 1]
    literal = re.sub(r"([{,]\s*)([A-Za-z_][A-Za-z0-9_]*)\s*:", r'\1"\2":', literal)
    literal = re.sub(r",(\s*[}\]])", r"\1", literal)
    return json.loads(literal)


def parse_cost(cost: str) -> float | None:
    """A number only when the listing states one. 'Free' is 0; 'Fee' is not stated."""
    if cost.strip().lower().startswith("free"):
        return 0.0
    match = re.search(r"\$\s*(\d+(?:\.\d+)?)", cost)
    return float(match.group(1)) if match else None


def explorer_records(explorer: Path) -> list[dict]:
    data_path = explorer / "prototype" / "trailskills-org-2" / "src" / "data.json"
    samples_path = explorer / "prototype" / "trailskills-org-2" / "src" / "data-samples.js"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    skills = {s["id"]: s for s in data["framework"]["skills"]}
    commit = git_head(explorer)
    origin = {"repository": "flexion/flexion-trailskills2.0-career-explorer", "commit": commit}

    def ref(skill_id: str, level: str) -> dict:
        skill = skills[skill_id]
        return {
            "category": CATEGORY[skill["categoryId"]],
            "skill": skill["name"],
            "required_level": LEVEL[level],
        }

    records = []
    for role in data["roles"]:
        records.append({
            "id": f"trailskills:role:{role['id']}",
            "scope": "trailskills",
            "kind": "role",
            "title": role["title"],
            "synthetic": False,
            "fixture": False,
            "source": {**origin, "path": data_path.relative_to(explorer).as_posix(), "role_id": role["id"],
                       "note": role.get("source", "")},
            "data": {
                "role": role["title"],
                "description": role.get("description", ""),
                "required_skills": [ref(r["skillId"], r["level"]) for r in role["requirements"]],
                # Optional depending on the job. Not a requirement, so not a gap.
                "role_dependent": [ref(r["skillId"], r["level"]) for r in role.get("roleDependent", [])],
                "volunteer": bool(role.get("volunteer")),
            },
        })

    for course in js_object_literal(samples_path.read_text(encoding="utf-8")):
        records.append({
            "id": f"trailskills:training:{course['id']}",
            "scope": "trailskills",
            "kind": "training",
            "title": course["title"],
            "synthetic": False,
            "fixture": False,
            "source": {**origin, "path": samples_path.relative_to(explorer).as_posix(), "course_id": course["id"],
                       "note": "prototype sample listing; competency alignment is a draft, not steward-approved"},
            "data": {
                "title": course["title"],
                "provider": course.get("provider", ""),
                "format": course.get("format", ""),
                "where": course.get("where", ""),
                "when": course.get("when", ""),
                "cost": course.get("cost", ""),
                "cost_usd": parse_cost(course.get("cost", "")),
                "proves": course.get("proves", ""),
                "skills_taught": [ref(skill_id, level) for skill_id, level in course.get("comps", [])],
                # BR-3.6: an alignment drives a next step only once a steward approved it.
                "alignment_approved": False,
            },
        })
    return records


def framework(explorer: Path) -> dict:
    """The framework itself, for AI-1 and AI-2 (the pivot of 2026-10-28): the 55
    competencies with their one-line definitions, each role's requirements by
    competency id, and the prototype's rule-based experience mapping (the
    fallback the spec names). Level text per competency is not in the repo; it
    lives on trailskills.org at each competency's url."""
    data_path = explorer / "prototype" / "trailskills-org-2" / "src" / "data.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    fw = data["framework"]
    return {
        "source": {"repository": "flexion/flexion-trailskills2.0-career-explorer", "commit": git_head(explorer),
                   "path": data_path.relative_to(explorer).as_posix()},
        "categories": [{"id": c["id"], "name": CATEGORY[c["id"]], "prototype_name": c["name"]} for c in fw["categories"]],
        "competencies": [{"id": s["id"], "category_id": s["categoryId"], "category": CATEGORY[s["categoryId"]],
                          "name": s["name"], "definition": s["definition"], "url": s["url"]} for s in fw["skills"]],
        "roles": [{"id": r["id"], "title": r["title"], "volunteer": bool(r.get("volunteer")),
                   "requirements": [{"skill_id": x["skillId"], "level": LEVEL[x["level"]]} for x in r["requirements"]],
                   "role_dependent": [{"skill_id": x["skillId"], "level": LEVEL[x["level"]]} for x in r.get("roleDependent", [])]}
                  for r in data["roles"]],
        "backgrounds": [{"id": b["id"], "label": b["label"], "keywords": b["keywords"],
                         "suggestions": [{"skill_id": x["skillId"], "level": LEVEL[x["level"]], "confidence": x.get("confidence")}
                                         for x in b["suggestions"]]} for b in data["experience"]["backgrounds"]],
        "keyword_rules": [{"match": k["match"], "skill_id": k["skillId"], "level": LEVEL[k["level"]], "confidence": k.get("confidence")}
                          for k in data["experience"]["keywordRules"]],
    }


def scenario_records(path: Path, *, fixture: bool) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        data = row["data"]
        records.append({
            "id": row["id"],
            "scope": row["profile_id"],
            "kind": row["kind"],
            "title": data.get("role") or data.get("title"),
            "synthetic": bool(row.get("synthetic", not fixture)),
            "fixture": fixture,
            "source": row["source"],
            "data": data,
        })
    return records


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--explorer", type=Path, default=EXPLORER_DEFAULT,
                        help="clone of flexion-trailskills2.0-career-explorer")
    args = parser.parse_args()

    records: list[dict] = []
    if args.explorer.exists():
        records += explorer_records(args.explorer)
        FRAMEWORK_OUT.write_text(json.dumps(framework(args.explorer), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"wrote {FRAMEWORK_OUT.relative_to(ROOT)}")
    else:
        print(f"warning: {args.explorer} not found; the trailskills scope is left out", file=sys.stderr)
    records += scenario_records(FIXTURES, fixture=True)
    if TC2.exists():
        records += scenario_records(TC2, fixture=False)

    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise SystemExit("duplicate record id; refusing to write")

    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in records), encoding="utf-8")
    by_scope: dict[str, int] = {}
    for r in records:
        key = "tc2-profile-*" if r["scope"].startswith("tc2-") else r["scope"]
        by_scope[key] = by_scope.get(key, 0) + 1
    print(f"wrote {len(records)} records to {OUT.relative_to(ROOT)}")
    for scope, n in by_scope.items():
        print(f"  {scope}: {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
