"""The prototype's vocabulary in, the prototype's vocabulary out. No model, no wiki.

    uv run python check_trailapp.py [path/to/career-explorer]

Chips only, so the answer comes from the framework lookup. Checks against the prototype's
own data.json that every id we return is one it knows, and that each mapped chip returns
the skills the prototype's chip suggests (minus the ones build_corpus.py drops on purpose).
"""

import json
import sys
from pathlib import Path

from suggest import suggest
from trailapp import BACKGROUNDS, PrototypeRequest, to_prototype, to_request

HERE = Path(__file__).resolve().parent
EXPLORER = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE.parents[2] / "flexion-trailskills2.0-career-explorer"
DATA = EXPLORER / "prototype" / "prototype-iterations" / "src" / "data.json"
# build_corpus.DROP_SUGGESTIONS: a chip alone says nothing about trail construction.
DROPPED = {("military", "mechanized-trail-construction")}

if not DATA.exists():
    sys.exit(f"career-explorer prototype data not found at {DATA}; pass the repo path")
data = json.loads(DATA.read_text(encoding="utf-8"))
known_skills = {s["id"] for s in data["framework"]["skills"]}
chips = {b["id"]: b for b in data["experience"]["backgrounds"]}

unknown = set(BACKGROUNDS) - set(chips)
assert not unknown, f"mapped chips the prototype does not have: {unknown}"

for chip_id, chip in chips.items():
    out = to_prototype(suggest(to_request(PrototypeRequest(backgrounds=[chip_id]))))
    got = [s["skillId"] for s in out["suggestions"]]
    want = [s["skillId"] for s in chip["suggestions"] if (chip_id, s["skillId"]) not in DROPPED]
    assert set(got) <= known_skills, f"{chip_id}: ids the prototype does not know: {set(got) - known_skills}"
    assert set(got) == set(want), f"{chip_id}: got {sorted(got)}, prototype suggests {sorted(want)}"
    # A chip alone never pre-checks (TC5, fix #3).
    assert not any(s["keep"] for s in out["suggestions"]), f"{chip_id}: a chip alone pre-checked a skill"
    assert all(s["level"] == "entry" and s["conf"] == "check" for s in out["suggestions"])
    print(f"{chip_id}: {len(got)} suggestions")

# A rejected id arrives in the prototype's spelling and must not come back.
theirs = "drainage-features-water-management"
out = to_prototype(suggest(to_request(PrototypeRequest(backgrounds=["trail-volunteering-corps"], rejected=[theirs]))))
assert theirs not in [s["skillId"] for s in out["suggestions"]]
print("ok: chips map, ids round-trip, nothing pre-checked, rejected stays rejected")
