# TC3 source data inspection

Inspected on 2026-10-26. This is a data preparation report, not the retrieval
technique comparison or the Week 3 architecture decision.

## Finding

The recovered TC2 dataset can support experiments over **fictional scenarios**.
It cannot currently supply valid role requirements to the existing Pathfinder
app: none of its 117 distinct required category/skill pairs are in the app's
framework. All 35 profiles pass the Pydantic input/output schemas, but all 35
return `needs_review=true` when passed to `pathfinder.solve(use_model=False)`.
Schema validity did not validate the free-text skill names.

The original file is unchanged. No skills were renamed, no scenarios were
merged, and no framework validation was weakened.

## Inventory

| Item | Count |
| --- | ---: |
| Synthetic profiles | 35 |
| Distinct role names | 31 |
| Scenario-specific role records | 35 |
| Required-skill occurrences | 132 |
| Distinct required category/skill pairs | 117 |
| Required category/skill pairs matching the app framework | 0 |
| Training records / distinct training titles | 70 / 70 |
| Trainings with simulated approval true / false | 50 / 20 |
| Role names with differing requirement sets | 4 |
| Repeated training titles with conflicting definitions | 0 |

Approval flags describe the invented scenarios. They do not establish real
steward approval, real course availability, or real prices. Distinct training
titles also do not prove that the offerings represent different real courses.

## What was separated

`data/retrieval_sources.jsonl` contains 105 proposed source records:

- 35 role records, retaining the role name and its complete required-skill list.
- 70 training records, retaining the original title, skills/levels taught,
  cost, completion evidence, and simulated approval flag.

These are facts *asserted by each synthetic input*, not verified domain facts.
Each record carries `synthetic: true` and a `profile_id` identifying its scenario.
The role's full requirement list remains together; no arbitrary text chunking
has been introduced. These are candidate evidence units to review before the
retrieval experiment, not a measured choice of chunking strategy.

Self-ratings are scenario inputs, not shared catalog knowledge. They are kept
in `data/retrieval_manifest.json` alongside each profile's source references.
Generated `output`, explanatory `why`, and generation labels `_axes` are
excluded from the source records. Retrieving those answers would contaminate
the experiment with the generator's conclusions.

## Conflicting role definitions

Profile numbers below are one-based physical lines in the unchanged original.
These names have different requirement sets; none identifies a single role
definition across the dataset.

| Role | Source profiles |
| --- | --- |
| Watershed Access Coordinator | 5, 25 |
| Watershed Trail Steward | 7, 30 |
| Backcountry Access Coordinator | 8, 20 |
| Backcountry Operations Coordinator | 16, 31 |

For example, profile 5's Watershed Access Coordinator requires Volunteer
Scheduling, Conflict De-escalation, and Stakeholder Mapping. Profile 25's
same-named role requires Culvert Inlet Clearing, Visitor Route Scoping, Shift
Handoff Briefing, and Grant Deliverable Tracking. Combining them would invent
a third definition that neither source supplies.

Keep each scenario's role and catalog slice together when exploring this data.
A role name alone is insufficient for the four cases above. An empty training
slice means no offering was supplied for that scenario, not proof that no
training exists anywhere. Cross-profile catalog pooling has not been justified.

## Traceability and reproduction

The original dataset's SHA-256 is:

`d18d661f2bbcf7036d55474f50be70569e758afaffff62fc64f062e26d28c2e1`

Profile IDs are `tc2-profile-<SHA-256 of canonical input JSON>`. Role IDs add
`:role`; training IDs add `:training-<SHA-256 of canonical training JSON>`.
They survive file reordering and changes to generated answers. Changing the
input scenario changes its ID, preventing silent reuse of old labels.

Each source record also identifies the original file, file checksum, physical
line, and JSON pointer(s). The manifest maps original profiles to their role
and training IDs and includes each original row's checksum, the full conflict
listing, unknown skills, and the actual app's review reason for every profile.

With the repository dependencies installed, regenerate the two local files:

```sh
uv run python use_case/prepare_retrieval_data.py
```

The script uses the existing Request/Response models and calls the existing
solver with `use_model=False`. It makes no model calls. Both derived data
files remain gitignored under `use_case/data/`, just like the original.

## What needs deciding before app integration

Recover or obtain the intended role definitions and category-scoped competency
mappings, then decide with the product owner whether to rebuild the synthetic
profiles against those definitions. Any mapping from invented skills to real
skills needs review; a similar name is not evidence of equivalence.

The current data can be used for clearly labelled retrieval mechanics
experiments, but successful retrieval alone cannot make it pass Pathfinder's
existing domain checks. The endpoint work needs this mismatch resolved first.
