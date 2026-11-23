# Text beats chips: conflict eval output

Measured 2026-11-23 by `uv run python use_case/evals/conflict_eval.py` (3 runs per case, live endpoint, tool way, `LLM_MODEL` from `.env`). This run is on the current `suggest.py`, which includes the TC6 evidence check and inline rules, so it is not the code the Week 5 post described.

| metric | result |
| --- | --- |
| `text_beats_chips` | **0.67** over 6 cases × 3 runs |
| `found_skills` (recall of skills she described) | **0.61** over 9 golden rows × 3 runs |

Per case: `t-conf-01` 2/3, `t-conf-02` 0/3, `t-conf-03` 3/3, `t-conf-04` 3/3, `t-conf-05` 1/3, `t-conf-06` 3/3.

What failed: `t-conf-02` (the minimal pair of 01) never pre-checked the drainage skill her words describe; `t-conf-05` left the new skill her text names (`water-crossing-structures-…`) at `check` in 2 of 3 runs; `t-conf-01` pre-checked `tread-hardening` once although her words point away from it. The chip-only rule itself (`t-conf-06`, silent chips are not contradicted) held 3/3.

So the post's "proving the worker's own words beat the chips" is not shown by this run: text wins when it contradicts a chip (03, 04, 06) and usually loses when it adds a skill the chips do not have (02, 05).

## Raw output

```
t-conf-01  points_away_never_did
   run 1: pass
           gave: tread-hardening:check, retaining-walls:check, tread-maintenance-mechanized-equipment:check, water-management-drainage-features:check
   run 2: pass
           gave: corridor-clearing-pruning-side-cutting-brushing:likely, tread-hardening:check, retaining-walls:check, tread-maintenance-mechanized-equipment:check, water-management-drainage-features:check
   run 3: FAIL pre-checked but her words point away: tread-hardening
           gave: corridor-clearing-pruning-side-cutting-brushing:likely, tread-hardening:possible, retaining-walls:check, tread-maintenance-mechanized-equipment:check, water-management-drainage-features:check
   -> 2/3

t-conf-02  minimal_pair_of_01
   run 1: FAIL not pre-checked: water-management-drainage-features or water-management-drainage-features-2
           gave: retaining-walls:likely, tread-hardening:possible, tread-maintenance-mechanized-equipment:possible, water-management-drainage-features:check
   run 2: FAIL not pre-checked: water-management-drainage-features or water-management-drainage-features-2
           gave: retaining-walls:likely, tread-hardening:possible, tread-maintenance-mechanized-equipment:possible, water-management-drainage-features:check
   run 3: FAIL not pre-checked: water-management-drainage-features or water-management-drainage-features-2
           gave: retaining-walls:likely, tread-hardening:possible, tread-maintenance-mechanized-equipment:possible, water-management-drainage-features:check
   -> 0/3

t-conf-03  points_away_different_work
   run 1: pass
           gave: water-crossing-structures-boardwalk-puncheon-turnpike-ford:check, retaining-walls:check, mechanized-trail-construction:check, construction-specifications:check, jobsite-safety:check
   run 2: pass
           gave: water-crossing-structures-boardwalk-puncheon-turnpike-ford:check, retaining-walls:check, mechanized-trail-construction:check, construction-specifications:check, jobsite-safety:check
   run 3: pass
           gave: water-crossing-structures-boardwalk-puncheon-turnpike-ford:check, retaining-walls:check, mechanized-trail-construction:check, construction-specifications:check, jobsite-safety:check
   -> 3/3

t-conf-04  text_beats_chip
   run 1: pass
           gave: water-management-drainage-features:likely, hand-built-trail-construction:likely, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut:check, corridor-clearing-felling-tree-removal-chainsaw-crosscut:check, safety-site-management-2:possible, corridor-clearing-material-and-debris-management:possible
   run 2: pass
           gave: water-management-drainage-features:likely, hand-built-trail-construction:likely, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut:check, corridor-clearing-felling-tree-removal-chainsaw-crosscut:check, safety-site-management-2:possible, corridor-clearing-material-and-debris-management:possible
   run 3: pass
           gave: water-management-drainage-features:likely, tread-hardening:likely, hand-built-trail-construction:likely, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut:check, corridor-clearing-felling-tree-removal-chainsaw-crosscut:check, safety-site-management-2:possible, corridor-clearing-material-and-debris-management:possible
   -> 3/3

t-conf-05  text_beats_chip_new_skill
   run 1: pass
           gave: water-crossing-structures-boardwalk-puncheon-turnpike-ford:likely, tread-maintenance-hand-tools:check, corridor-clearing-power-tools:check, safety-site-management-2:possible, water-management-drainage-features-2:check
   run 2: FAIL not pre-checked: water-crossing-structures-boardwalk-puncheon-turnpike-ford
           gave: hand-built-trail-construction:likely, tread-maintenance-hand-tools:check, corridor-clearing-power-tools:possible, safety-site-management-2:possible, water-management-drainage-features-2:check
   run 3: FAIL not pre-checked: water-crossing-structures-boardwalk-puncheon-turnpike-ford
           gave: hand-built-trail-construction:likely, tread-hardening:likely, tread-maintenance-hand-tools:check, corridor-clearing-power-tools:possible, safety-site-management-2:possible, water-management-drainage-features-2:check
   -> 1/3

t-conf-06  silent_is_not_contradicted
   run 1: pass
           gave: crew-management:likely, crew-training:likely, communications:likely, jobsite-safety:likely
   run 2: pass
           gave: crew-management:likely, crew-training:likely, communications:likely, jobsite-safety:likely
   run 3: pass
           gave: crew-management:likely, crew-training:likely, communications:likely, jobsite-safety:likely
   -> 3/3


text_beats_chips: 0.67 over 6 cases x 3 runs

found_skills (recall of skills she described), 9 golden rows x 3 runs
   t-ai1-01  0.67   runs: 0.67, 0.67, 0.67
   t-ai1-03  0.58   runs: 0.75, 0.50, 0.50
   t-ai1-04  0.67   runs: 0.67, 0.67, 0.67
   t-ai1-05  0.87   runs: 1.00, 0.80, 0.80
   t-ai1-08  0.00   runs: 0.00, 0.00, 0.00
   t-ai1-11  0.50   runs: 0.50, 0.50, 0.50
   t-ai1-12  0.83   runs: 0.75, 0.75, 1.00
   t-ai1-13  0.58   runs: 0.75, 0.50, 0.50
   t-ai1-14  0.78   runs: 0.67, 1.00, 0.67
found_skills: 0.61
```
