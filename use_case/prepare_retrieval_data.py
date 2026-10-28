"""Inspect TC2 profiles and extract traceable synthetic source facts.

Run from the repository root:
    uv run python use_case/prepare_retrieval_data.py

Uses the existing schema and solver, with model calls disabled. The source
dataset is never edited. Derived JSON files remain under gitignored data/.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from hashlib import sha256
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "01_Product_Engineering" / "challenge"))

from pathfinder import FRAMEWORK_SKILLS, solve
from schema import Request, Response

DATA = ROOT / "use_case" / "data"
SOURCE = DATA / "synthetic_v1.jsonl"


def canonical(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value: object) -> str:
    return sha256(canonical(value).encode()).hexdigest()


def name_key(name: str) -> str:
    return " ".join(name.casefold().split())


def main() -> None:
    source_bytes = SOURCE.read_bytes()
    dataset_hash = sha256(source_bytes).hexdigest()
    records = []
    profiles = []
    roles = defaultdict(list)
    trainings = defaultdict(list)
    known = {(category.value, skill) for category, skills in FRAMEWORK_SKILLS.items() for skill in skills}
    required_pairs = set()
    unknown_pairs = set()
    approval_counts = Counter()
    requirement_count = 0

    for line_number, line in enumerate(source_bytes.decode("utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        request = Request.model_validate(row["input"])
        Response.model_validate(row["output"])
        inputs = row["input"]
        # Full input hashes keep identity stable across file reordering and
        # changes to generated answers. A changed scenario gets a new identity.
        profile_id = "tc2-profile-" + fingerprint(inputs)
        role_id = profile_id + ":role"
        provenance = {
            "path": SOURCE.relative_to(ROOT).as_posix(),
            "sha256": dataset_hash,
            "line": line_number,
        }
        role_data = {key: inputs[key] for key in ("role", "required_skills")}
        records.append({
            "id": role_id,
            "kind": "role",
            "profile_id": profile_id,
            "synthetic": True,
            "source": {**provenance, "json_pointers": ["/input/role", "/input/required_skills"]},
            "data": role_data,
        })
        # Ignore requirement ordering when detecting different definitions of
        # the same role. Preserve the original order in the extracted record.
        signature = canonical(sorted(inputs["required_skills"], key=canonical))
        roles[name_key(inputs["role"])].append({
            "role": inputs["role"], "line": line_number,
            "id": role_id, "signature": signature,
        })
        training_ids = []
        for index, training in enumerate(inputs.get("trainings", [])):
            training_id = profile_id + ":training-" + fingerprint(training)
            training_ids.append(training_id)
            records.append({
                "id": training_id,
                "kind": "training",
                "profile_id": profile_id,
                "synthetic": True,
                "source": {**provenance, "json_pointers": [f"/input/trainings/{index}"]},
                "data": training,
            })
            trainings[name_key(training["title"])].append({
                "title": training["title"], "line": line_number,
                "id": training_id, "signature": canonical(training),
            })
            approval_counts[str(training.get("alignment_approved", False)).lower()] += 1

        pairs = {(s["category"], s["skill"]) for s in inputs["required_skills"]}
        required_pairs.update(pairs)
        unknown_pairs.update(pairs - known)
        requirement_count += len(inputs["required_skills"])
        # Exercise the actual app guard, rather than assuming schema validity
        # implies compatibility with the framework.
        result = solve(request, use_model=False)
        profiles.append({
            "id": profile_id,
            "source": provenance,
            "row_sha256": fingerprint(row),
            "role_id": role_id,
            "training_ids": training_ids,
            "self_ratings": inputs["self_ratings"],
            "needs_review": result.needs_review,
            "review_reason": result.review_reason,
        })

    ids = [record["id"] for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source identity; inspect duplicate profiles or trainings before exporting")

    def conflicts(groups: dict) -> list:
        return [
            [{k: v for k, v in item.items() if k != "signature"} for item in items]
            for items in groups.values()
            if len({item["signature"] for item in items}) > 1
        ]

    role_conflicts = conflicts(roles)
    training_conflicts = conflicts(trainings)
    manifest = {
        "format_version": 1,
        "dataset_sha256": dataset_hash,
        "scope": "Synthetic scenario facts only; not a verified role library or training catalog.",
        "excluded_from_source_records": ["input.self_ratings", "output", "why", "_axes"],
        "scope_rule": "Keep role and training evidence within one profile_id; do not resolve repeated role names by merging scenarios.",
        "summary": {
            "profiles": len(profiles),
            "role_names": len(roles),
            "role_records": len(profiles),
            "requirement_occurrences": requirement_count,
            "unique_required_category_skill_pairs": len(required_pairs),
            "unknown_required_category_skill_pairs": len(unknown_pairs),
            "training_records": sum(approval_counts.values()),
            "training_titles": len(trainings),
            "simulated_alignment_approval": dict(approval_counts),
            "conflicting_role_names": len(role_conflicts),
            "conflicting_training_titles": len(training_conflicts),
            "profiles_requiring_review": sum(p["needs_review"] for p in profiles),
        },
        "role_conflicts": role_conflicts,
        "training_conflicts": training_conflicts,
        "unknown_required_skills": [
            {"category": category, "skill": skill} for category, skill in sorted(unknown_pairs)
        ],
        "profiles": profiles,
    }
    if SOURCE.read_bytes() != source_bytes:
        raise RuntimeError("Source dataset changed during inspection; rerun before exporting")
    (DATA / "retrieval_sources.jsonl").write_text(
        "".join(json.dumps(record, ensure_ascii=False) + "\n" for record in records), encoding="utf-8"
    )
    (DATA / "retrieval_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest["summary"], indent=2))
    print("Wrote use_case/data/retrieval_sources.jsonl and retrieval_manifest.json")


if __name__ == "__main__":
    main()
