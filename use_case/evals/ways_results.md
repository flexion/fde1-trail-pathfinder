# TC5: the tool loop vs the skill, measured

Measured 2026-11-10 by `ways_compare.py`, in-process through `suggest()`, model `LLM_MODEL` from `.env` through the gateway. Median of the runs, range in brackets. Tokens are everything that crossed the model boundary (prompt + completion, all calls).

Requests: `t-ai1-01` is one kind of work (hand trail work on a corps crew) with the `corps` chip. `t-ai1-13` is the multi-topic one, chosen over `t-ai1-03` because it names four unrelated kinds of work (volunteer coordination, a newsletter, a grant, drain clearing and brushing) and no chip, so every skill has to come from searches; `t-ai1-03`'s saw work and supervision overlap and its `forestry` chip supplies skills with no search.

Capability calls: the tool way's count is a counting wrapper passed as `search=`. The skill way's in-process count is the same wrapper's view (it never runs); the far-side count is the `capability_call search_chunks` lines `run.py` prints on stderr.

## Step 4: demo scale (k left to the model / run.py default)

| way | request | model calls | capability calls | tool calls on turn 1 | latency ms | tokens | payload bytes in context | suggestions | declined | response bytes | errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tool | t-ai1-01 | 3 (2–3) | 8 (5–8) | 4 (4–5) | 7034 (5346–11658) | 7009 (3917–7396) | 12924 (9221–12970) | 8 | 0/3 | 2855 (2855–2997) | 0/3 |
| skill | t-ai1-01 | 2 | 0 in-process / 1 far side | 1 | 9804 (7739–10710) | 2674 (2407–2955) | 1616 (1454–1641) | 8 (7–8) | 0/3 | 2911 (2561–3056) | 0/3 |
| tool | t-ai1-13 | 3 (2–3) | 4 (3–8) | 3 (3–4) | 4879 (3679–5323) | 4517 (2984–5412) | 8820 (7254–11135) | 4 (3–5) | 0/3 | 1545 (1250–1862) | 0/3 |
| skill | t-ai1-13 | 2 | 0 in-process / 4 (1–4) far side | 1 | 12298 (5784–13859) | 2499 (1545–2702) | 5682 (1206–6117) | 4 (3–5) | 0/3 | 1564 (1231–2074) | 0/3 |

Turn 1 for the skill way is the plan call, which must emit exactly one `plan_searches` call; the number of searches it planned is the far-side capability count.

## Step 5: payload size, `t-ai1-13`, k forced

| way | k | bytes per search (median) | capability calls | model calls | prompt tokens | tokens | latency ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| tool | 1 | 370 | 9 (7–9) | 3 (3–4) | 2431 (2191–3606) | 3047 (2819–4550) | 5119 (5000–7669) |
| skill | 1 | 281 | 0 in-process / 4 far side | 2 | 1163 (1161–1182) | 1536 (1484–1575) | 12463 (5662–13175) |
| tool | 4 | 1511 | 8 (4–8) | 3 (3–4) | 4690 (3302–7388) | 5466 (3974–8194) | 6078 (4654–6730) |
| skill | 4 | 1479 | 0 in-process / 3 (1–4) far side | 2 | 1810 (1212–2051) | 2240 (1607–2543) | 10209 (5370–13639) |
| tool | 8 | 3068 | 4 (4–5) | 3 (2–3) | 5337 (3217–5521) | 6009 (3724–6130) | 3808 (3443–4804) |
| skill | 8 | 2879 | 0 in-process / 4 (1–4) far side | 2 | 3051 (1493–3061) | 3719 (1853–3810) | 14049 (5033–15068) |

## Did the two ways suggest the same skills? (Step 4 runs)

- `t-ai1-01` tool: text-path skill ids per run `corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut, corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, water-management-drainage-features-2` ×1; `corridor-clearing-felling-tree-removal-chainsaw-crosscut, corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, water-management-drainage-features-2` ×2
  pre-checked: `corridor-clearing-power-tools, corridor-clearing-pruning-side-cutting-brushing, safety-site-management-2, trail-sustainability-principles, tread-maintenance-hand-tools, water-management-drainage-features-2` ×2; `corridor-clearing-power-tools, corridor-clearing-pruning-side-cutting-brushing, safety-site-management-2, trail-sustainability-principles, water-management-drainage-features-2` ×1
- `t-ai1-01` skill: text-path skill ids per run `corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut, corridor-clearing-power-tools, corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, tread-maintenance-hand-tools, water-management-drainage-features-2` ×1; `corridor-clearing-felling-tree-removal-chainsaw-crosscut, corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, water-management-drainage-features-2` ×1; `corridor-clearing-power-tools, corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, tread-maintenance-hand-tools, water-management-drainage-features-2` ×1
  pre-checked: `corridor-clearing-power-tools, corridor-clearing-pruning-side-cutting-brushing, safety-site-management-2, trail-sustainability-principles, tread-maintenance-hand-tools, water-management-drainage-features-2` ×1; `corridor-clearing-pruning-side-cutting-brushing, safety-site-management-2, trail-sustainability-principles, tread-maintenance-hand-tools, water-management-drainage-features-2` ×2
  **t-ai1-01**: in every run, tool `corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, water-management-drainage-features-2`, skill `corridor-clearing-pruning-side-cutting-brushing, hand-built-trail-construction, water-management-drainage-features-2`. In some run of one way only: tool `—`, skill `corridor-clearing-power-tools, tread-maintenance-hand-tools`.
- `t-ai1-13` tool: text-path skill ids per run `communications, crew-management, funding-grants, water-management-drainage-features-2` ×1; `communications, education-and-public-outreach, funding-grants` ×1; `corridor-clearing-pruning-side-cutting-brushing-2, crew-management, education-and-public-outreach, funding-grants, water-management-drainage-features-2` ×1
  pre-checked: `communications, crew-management, water-management-drainage-features-2` ×1; `communications, education-and-public-outreach` ×1; `corridor-clearing-pruning-side-cutting-brushing-2, crew-management, education-and-public-outreach, water-management-drainage-features-2` ×1
- `t-ai1-13` skill: text-path skill ids per run `communications, education-and-public-outreach, funding-grants, water-management-drainage-features-2` ×1; `corridor-clearing-pruning-side-cutting-brushing-2, crew-management, education-and-public-outreach, funding-grants, water-management-drainage-features-2` ×1; `education-and-public-outreach, funding-grants, maintenance-specifications` ×1
  pre-checked: `communications, education-and-public-outreach, water-management-drainage-features-2` ×1; `corridor-clearing-pruning-side-cutting-brushing-2, crew-management, education-and-public-outreach, water-management-drainage-features-2` ×1; `education-and-public-outreach, maintenance-specifications` ×1
  **t-ai1-13**: in every run, tool `funding-grants`, skill `education-and-public-outreach, funding-grants`. In some run of one way only: tool `—`, skill `maintenance-specifications`.

## Real response size: the queries the tool loop actually sent, re-run at k=4

85 distinct queries; one `search_chunks` response is 984–1958 bytes, median 1474. Chunks are cut at 1,000 characters, so k=8 is at most about 8 KB.

Skill-way latency is mostly process start, not the boundary itself: a `run.py` whose query embedding is cached takes about 0.2 s; one with a new query imports litellm, calls Titan and rewrites the 5 MB `EMBED_CACHE` file, about 4.5 s, every time, in a fresh process.
