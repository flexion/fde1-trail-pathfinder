"""Build and check `retrieval-dataset.jsonl`, the data the Week 3 SQL path reads.

    python use_case/evals/retrieval_dataset.py          # write use_case/data/retrieval_dataset.jsonl (local, gitignored)
    python use_case/evals/retrieval_dataset.py --check  # verify it (CI-safe)

Thirteen scenarios cover all twelve cells of the two TC2 axes
(`training_availability` x `gap_count`, see `02_Open_Weights/challenge/axes.py`).
Four are copied from `golden.jsonl` so the ten questions in `retrieval.jsonl`
still resolve; nine are authored here, one for each cell the goldens miss.

Every record is invented. Skill names are the real framework names: the app
sends an unknown or wrong-category skill to the manual path, so a made-up skill
would test the wrong thing. `--check` derives each scenario's axes from the
repo's own `pathfinder` functions and fails if a declared tag is wrong, which
is the mislabelling the TC2 datasheet admits to for 4 of its 35 rows.

Ranking is kept unambiguous on purpose: wherever a close gap competes with a
missing one, the close gap's training is also free, so "close first" and "free
first" agree. Golden 6's open question (a $200 course against a free one that
closes two gaps) is not baked in either way.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data" / "retrieval_dataset.jsonl"  # use_case/data/ is gitignored: the data stays local
GOLDEN = HERE / "golden.jsonl"
QUESTIONS = HERE / "retrieval.jsonl"
APP = HERE.parent.parent / "01_Product_Engineering" / "challenge"

TC, TM, PD, CM, PA = (
    "Trail Construction",
    "Trail Maintenance",
    "Project Planning and Design",
    "Crew Management",
    "Program Administration",
)
ENTRY, FULL, EXPERT = "Entry", "Full Performance", "Expert"

# Golden line -> scenario id. Goldens 4 (unknown skill) and 6 (ranking unresolved) are out.
GOLDEN_SCENARIOS = {1: "golden-01", 2: "golden-02", 3: "golden-03", 5: "golden-05"}


def req(cat: str, skill: str, level: str) -> dict:
    return {"category": cat, "skill": skill, "required_level": level}


def rate(cat: str, skill: str, level: str | None) -> dict:
    return {"category": cat, "skill": skill, "level": level}


def training(title: str, taught: list[dict], cost: float, proves: str, approved: bool) -> dict:
    return {
        "title": title,
        "skills_taught": taught,
        "cost_usd": cost,
        "proves": proves,
        "alignment_approved": approved,
    }


# axes = (training_availability, gap_count)
AUTHORED = [
    {
        "id": "axis-01",
        "axes": ("training_exists_not_yet_approved", "zero_gaps"),
        "role": "Trail Crew Member",
        "required": [req(TC, "Hand-Built Trail Construction", ENTRY), req(TM, "Safety/Site Management", ENTRY)],
        "ratings": [rate(TC, "Hand-Built Trail Construction", FULL), rate(TM, "Safety/Site Management", ENTRY)],
        "trainings": [
            training("Site Safety Refresher", [req(TM, "Safety/Site Management", ENTRY)], 40,
                     "attendance record", False),
        ],
    },
    {
        "id": "axis-02",
        "axes": ("training_exists_not_yet_approved", "one_to_three_gaps"),
        "role": "Trail Crew Member",
        "required": [req(TM, "Tread Maintenance - Hand tools", FULL), req(TM, "Drainage Features/Water Management", ENTRY)],
        "ratings": [rate(TM, "Tread Maintenance - Hand tools", ENTRY), rate(TM, "Drainage Features/Water Management", ENTRY)],
        "trainings": [
            training("Advanced Tread Workshop", [req(TM, "Tread Maintenance - Hand tools", FULL)], 120,
                     "provider certificate of completion", False),
        ],
    },
    {
        "id": "axis-03",
        "axes": ("training_exists_not_yet_approved", "four_or_more_gaps"),
        "role": "Trail Crew Leader",
        "required": [
            req(CM, "Crew Training", FULL), req(CM, "Performance Management", ENTRY),
            req(CM, "Crew Recruitment", ENTRY), req(CM, "Jobsite Safety", FULL),
            req(PA, "Communications", ENTRY),
        ],
        "ratings": [
            rate(CM, "Crew Training", ENTRY), rate(CM, "Performance Management", None),
            rate(CM, "Crew Recruitment", None), rate(CM, "Jobsite Safety", ENTRY),
            rate(PA, "Communications", None),
        ],
        "trainings": [
            training("Leading Field Crews", [req(CM, "Crew Training", FULL), req(CM, "Performance Management", ENTRY)],
                     250, "provider certificate of completion", False),
            training("Crew Hiring Basics", [req(CM, "Crew Recruitment", ENTRY)], 0, "attendance record", False),
            training("Safety Leadership Day", [req(CM, "Jobsite Safety", FULL)], 90,
                     "provider certificate of completion", False),
        ],
    },
    {
        "id": "axis-04",
        "axes": ("multiple_trainings_match", "zero_gaps"),
        "role": "Trail Crew Member",
        "required": [
            req(TM, "Corridor Clearing: Pruning/ Side-Cutting/ Brushing", ENTRY),
            req(TC, "Trail Sustainability Principles", ENTRY),
        ],
        "ratings": [
            rate(TM, "Corridor Clearing: Pruning/ Side-Cutting/ Brushing", ENTRY),
            rate(TC, "Trail Sustainability Principles", FULL),
        ],
        "trainings": [
            training("Brushing Basics", [req(TM, "Corridor Clearing: Pruning/ Side-Cutting/ Brushing", ENTRY)], 0,
                     "attendance record", True),
            training("Pruning and Side-Cutting Clinic",
                     [req(TM, "Corridor Clearing: Pruning/ Side-Cutting/ Brushing", FULL)], 60,
                     "provider certificate of completion", True),
        ],
    },
    {
        "id": "axis-05",
        "axes": ("multiple_trainings_match", "one_to_three_gaps"),
        "role": "Trail Crew Member",
        "required": [req(TM, "Tread Maintenance - Hand tools", FULL), req(TM, "Safety/Site Management", ENTRY)],
        "ratings": [rate(TM, "Tread Maintenance - Hand tools", ENTRY), rate(TM, "Safety/Site Management", FULL)],
        "trainings": [
            training("Tread Skills Weekend", [req(TM, "Tread Maintenance - Hand tools", FULL)], 95,
                     "provider certificate of completion", True),
            training("Community Tread Day", [req(TM, "Tread Maintenance - Hand tools", FULL)], 0,
                     "attendance record from the host organization", True),
        ],
    },
    {
        "id": "axis-06",
        "axes": ("multiple_trainings_match", "four_or_more_gaps"),
        "role": "Trail Crew Leader",
        "required": [
            req(CM, "Crew Recruitment", ENTRY), req(CM, "Crew Training", FULL), req(CM, "Jobsite Safety", FULL),
            req(PA, "Inspections/Monitoring", ENTRY), req(PA, "Visitor Use Management", ENTRY),
        ],
        "ratings": [
            rate(CM, "Crew Recruitment", None), rate(CM, "Crew Training", ENTRY), rate(CM, "Jobsite Safety", None),
            rate(PA, "Inspections/Monitoring", None), rate(PA, "Visitor Use Management", None),
        ],
        "trainings": [
            training("Crew Training Workshop", [req(CM, "Crew Training", FULL)], 180,
                     "provider certificate of completion", True),
            training("Crew Training Self-Paced Course", [req(CM, "Crew Training", FULL)], 0,
                     "attendance record", True),
            training("Hiring and Onboarding", [req(CM, "Crew Recruitment", ENTRY)], 50,
                     "provider certificate of completion", True),
            training("Jobsite Safety Certification", [req(CM, "Jobsite Safety", FULL)], 120,
                     "provider certificate of completion", True),
            training("Visitor Use Basics", [req(PA, "Visitor Use Management", ENTRY)], 0,
                     "attendance record", True),
        ],
    },
    {
        "id": "axis-07",
        "axes": ("approved_training_exists", "four_or_more_gaps"),
        "role": "Trail Designer",
        "required": [
            req(PD, "Corridor Planning", ENTRY), req(PD, "Trail Specifications", FULL),
            req(PD, "Conceptual Trail Plan Development", ENTRY), req(PD, "Project Cost Estimation", ENTRY),
            req(PD, "Compliance and Permitting", ENTRY),
        ],
        "ratings": [
            rate(PD, "Corridor Planning", None), rate(PD, "Trail Specifications", ENTRY),
            rate(PD, "Conceptual Trail Plan Development", None), rate(PD, "Project Cost Estimation", None),
            rate(PD, "Compliance and Permitting", None),
        ],
        "trainings": [
            training("Trail Specs Workshop", [req(PD, "Trail Specifications", FULL)], 0,
                     "attendance record", True),
            training("Corridor Planning Primer", [req(PD, "Corridor Planning", ENTRY)], 40,
                     "provider certificate of completion", True),
            training("Cost Estimating for Trails", [req(PD, "Project Cost Estimation", ENTRY)], 75,
                     "provider certificate of completion", True),
            training("Concept Plan Studio", [req(PD, "Conceptual Trail Plan Development", ENTRY)], 150,
                     "provider certificate of completion", True),
        ],
    },
    {
        "id": "axis-08",
        "axes": ("no_training_available", "zero_gaps"),
        "role": "Trail Designer",
        "required": [req(PD, "Corridor Planning", ENTRY), req(PD, "Land Use Plan Alignment", ENTRY)],
        "ratings": [rate(PD, "Corridor Planning", FULL), rate(PD, "Land Use Plan Alignment", ENTRY)],
        "trainings": [],
    },
    {
        "id": "axis-09",
        "axes": ("no_training_available", "four_or_more_gaps"),
        "role": "Trail Crew Leader",
        "required": [
            req(CM, "Crew Training", FULL), req(CM, "Performance Management", ENTRY),
            req(CM, "Crew Management", ENTRY), req(CM, "Jobsite Safety", FULL),
            req(PA, "Communications", ENTRY),
        ],
        "ratings": [
            rate(CM, "Crew Training", ENTRY), rate(CM, "Performance Management", None),
            rate(CM, "Crew Management", None), rate(CM, "Jobsite Safety", None),
            rate(PA, "Communications", None),
        ],
        # A catalog that exists but teaches nothing this role needs: a harder decline than an empty one.
        "trainings": [
            training("Chainsaw Safety Basics",
                     [req(TM, "Corridor Clearing: Bucking, Felling/ Hazard Tree Removal; Chainsaw/ Crosscut", ENTRY)],
                     300, "provider certificate of completion", True),
        ],
    },
]

AXIS_NAMES = {
    "training_availability": {
        "approved_training_exists", "training_exists_not_yet_approved",
        "no_training_available", "multiple_trainings_match",
    },
    "gap_count": {"zero_gaps", "one_to_three_gaps", "four_or_more_gaps"},
}


def _records(sid: str, axes: tuple[str, str], origin: str, role: str, required: list[dict],
             ratings: list[dict], trainings: list[dict]) -> list[dict]:
    base = {"profile_id": sid, "axes": {"training_availability": axes[0], "gap_count": axes[1]}, "origin": origin}
    rows = [
        {"id": f"{sid}:role", **base, "kind": "role", "data": {"role": role, "required_skills": required}},
        {"id": f"{sid}:ratings", **base, "kind": "ratings", "data": {"self_ratings": ratings}},
    ]
    rows += [
        {"id": f"{sid}:training-{n:02d}", **base, "kind": "training", "data": t}
        for n, t in enumerate(trainings, 1)
    ]
    return rows


def _derive_axes(inp: dict) -> tuple[str, str]:
    """Axis values computed from the repo's own rules, never trusted from a tag."""
    sys.path.insert(0, str(APP))
    import pathfinder  # pyright: ignore[reportMissingImports]
    from schema import GapStatus, Request  # pyright: ignore[reportMissingImports]

    request = Request.model_validate(inp)
    gaps = pathfinder.compute_gaps(request)
    n_open = sum(g.status != GapStatus.HAS for g in gaps)
    gap_count = "zero_gaps" if n_open == 0 else "one_to_three_gaps" if n_open <= 3 else "four_or_more_gaps"

    # Judged against every required skill, not just open gaps, so a zero-gap profile has a catalog too.
    touching = [(t, r) for t in request.trainings for r in request.required_skills
                if any(s.category == r.category and s.skill == r.skill and
                       pathfinder.LEVEL_RANK[s.required_level] >= pathfinder.LEVEL_RANK[r.required_level]
                       for s in t.skills_taught)]
    approved = [(t, r) for t, r in touching if t.alignment_approved]
    per_skill: dict[tuple, int] = {}
    for _, r in approved:
        per_skill[(r.category, r.skill)] = per_skill.get((r.category, r.skill), 0) + 1
    if any(n >= 2 for n in per_skill.values()):
        availability = "multiple_trainings_match"
    elif approved:
        availability = "approved_training_exists"
    elif touching:
        availability = "training_exists_not_yet_approved"
    else:
        availability = "no_training_available"
    return availability, gap_count


def build() -> list[dict]:
    rows: list[dict] = []
    golden = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines() if line.strip()]
    for line_no, sid in GOLDEN_SCENARIOS.items():
        inp = golden[line_no - 1]["input"]
        axes = _derive_axes(inp)
        rows += _records(sid, axes, f"golden.jsonl line {line_no}", inp["role"],
                         inp["required_skills"], inp["self_ratings"], inp["trainings"])
    for s in AUTHORED:
        rows += _records(s["id"], s["axes"], "authored", s["role"], s["required"], s["ratings"], s["trainings"])
    return rows


def _scenario_input(rows: list[dict], sid: str) -> dict:
    mine = [r for r in rows if r["profile_id"] == sid]
    role = next(r for r in mine if r["kind"] == "role")["data"]
    ratings = next(r for r in mine if r["kind"] == "ratings")["data"]
    return {
        "role": role["role"],
        "required_skills": role["required_skills"],
        "self_ratings": ratings["self_ratings"],
        "trainings": [r["data"] for r in mine if r["kind"] == "training"],
    }


def check() -> list[str]:
    problems: list[str] = []
    rows = [json.loads(line) for line in OUT.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        problems.append("duplicate record ids")

    covered: dict[tuple[str, str], list[str]] = {}
    for sid in sorted({r["profile_id"] for r in rows}):
        kinds = {r["kind"] for r in rows if r["profile_id"] == sid}
        if not {"role", "ratings"} <= kinds:
            problems.append(f"{sid}: missing a role or ratings record")
            continue
        tagged = next(r for r in rows if r["profile_id"] == sid and r["kind"] == "role")["axes"]
        tag =(tagged["training_availability"], tagged["gap_count"])
        if tag[0] not in AXIS_NAMES["training_availability"] or tag[1] not in AXIS_NAMES["gap_count"]:
            problems.append(f"{sid}: unknown axis value {tag}")
            continue
        derived = _derive_axes(_scenario_input(rows, sid))
        if derived != tag:
            problems.append(f"{sid}: tagged {tag} but the repo's rules give {derived}")
        covered.setdefault(derived, []).append(sid)

    for a in sorted(AXIS_NAMES["training_availability"]):
        for g in sorted(AXIS_NAMES["gap_count"]):
            if (a, g) not in covered:
                problems.append(f"axis cell not covered: {a} x {g}")

    # Four-or-more must actually force the cap to cut, or the cell tests nothing.
    sys.path.insert(0, str(APP))
    import pathfinder  # pyright: ignore[reportMissingImports]
    from schema import REC_MAX, Request  # pyright: ignore[reportMissingImports]

    four_plus = [sid for cell, sids in covered.items() if cell[1] == "four_or_more_gaps" for sid in sids]
    for sid in four_plus:
        availability = _derive_axes(_scenario_input(rows, sid))[0]
        if availability not in ("approved_training_exists", "multiple_trainings_match"):
            continue  # no approved training, so there is nothing for the cap to cut
        req_ = Request.model_validate(_scenario_input(rows, sid))
        open_gaps = [g for g in pathfinder.compute_gaps(req_) if g.status != "has"]
        closable = sum(any(pathfinder._closes(t, g) for t in req_.trainings) for g in open_gaps)
        if closable <= REC_MAX:
            problems.append(f"{sid}: only {closable} closable gaps, the cap of {REC_MAX} never cuts")

    # Every gold id in the question file must exist here, in the right scenario.
    by_id = {r["id"]: r for r in rows}
    for line in QUESTIONS.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        q = json.loads(line)
        for gid in q["gold"]:
            rec = by_id.get(gid)
            if rec is None:
                problems.append(f"{q['id']}: gold {gid} not in the dataset")
            elif rec["profile_id"] != q["context"]["profile_id"]:
                problems.append(f"{q['id']}: gold {gid} belongs to {rec['profile_id']}, not the question's scenario")
    return problems


def main() -> int:
    if "--check" in sys.argv:
        problems = check()
        for p in problems:
            print("FAIL", p)
        print("ok" if not problems else f"{len(problems)} problem(s)")
        return 1 if problems else 0
    rows = build()
    OUT.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    print(f"wrote {len(rows)} records, {len({r['profile_id'] for r in rows})} scenarios -> {OUT.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
