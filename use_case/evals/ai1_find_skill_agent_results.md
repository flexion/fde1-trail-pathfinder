# AI-1 step 1, model + tools (Agentic RAG and DCI)

Model: `openai/bedrock/gpt-5.6-luna`. bm25/dense: 220 chunks from 55 wiki pages (split at `##`); dci: the 55 pages and the index. Max 6 turns, k capped at 8. **3 runs per case**: each cell is the mean, with the range across runs in brackets. Twins (the same skill under two categories) count as one gold skill: either passes.

| technique | all gold found (of 8) | gold recall | wrong named | declines correct (of 2) | quotes not in her text | calls | evidence chars | s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 3.0 (2.0–4.0) | 75% (68%–79%) | 2.3 (2.0–3.0) | 2.0 | 0.0 | 4.0 (3.7–4.3) | 7,163 (6,738–7,626) | 3.5 (3.0–4.2) |
| dense | 4.3 (4.0–5.0) | 87% (86%–89%) | 2.7 (2.0–3.0) | 1.7 (1.0–2.0) | 0.7 (0.0–1.0) | 3.9 (3.9–4.0) | 7,090 (6,796–7,300) | 4.7 (4.6–4.9) |
| dci | 3.7 (3.0–4.0) | 76% (71%–82%) | 2.7 (2.0–3.0) | 2.0 | 1.0 | 4.7 (4.2–5.2) | 13,428 (12,103–15,994) | 3.6 (3.3–4.0) |

## bm25

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 2/3 | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut-2 | 4.3 | 6,584 | 4.3 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×3 | - | 3.7 | 5,931 | 3.4 |
| retrieval-03 | multi-hop | 3/3 | - | tread-hardening | 5.3 | 9,392 | 4.5 |
| retrieval-04 | multi-hop | 0/3 | hand-built-trail-construction ×3, jobsite-safety ×3 | - | 5.7 | 8,535 | 4.2 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 2.7 | 5,308 | 2.6 |
| retrieval-06 | multi-hop | 1/3 | tread-hardening ×2, mechanized-trail-construction | - | 5.7 | 8,340 | 4.3 |
| retrieval-07 | decline | 3/3 | - | - | 1.3 | 3,142 | 2.1 |
| retrieval-08 | decline | 3/3 | - | - | 2.0 | 4,020 | 2.1 |
| retrieval-09 | multi-hop | 0/3 | corridor-clearing-pruning-side-cutting-brushing-2 ×3, water-management-drainage-features-2 ×2 | corridor-clearing-power-tools, crew-management | 6.7 | 15,194 | 5.2 |
| retrieval-10 | multi-hop | 3/3 | - | - | 3.0 | 5,185 | 2.2 |

## dense

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 3/3 | - | - | 4.0 | 5,882 | 3.4 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×3 | - | 3.3 | 6,407 | 4.9 |
| retrieval-03 | multi-hop | 3/3 | - | tread-hardening | 5.3 | 10,922 | 6.0 |
| retrieval-04 | multi-hop | 0/3 | jobsite-safety ×3 | - | 5.0 | 7,971 | 5.8 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 4.0 | 5,787 | 5.5 |
| retrieval-06 | multi-hop | 2/3 | mechanized-trail-construction | - | 5.3 | 8,402 | 5.5 |
| retrieval-07 | decline | 3/3 | - | - | 1.0 | 2,422 | 2.1 |
| retrieval-08 | decline | 2/3 | - | crew-management | 3.0 | 7,816 | 3.8 |
| retrieval-09 | multi-hop | 2/3 | corridor-clearing-pruning-side-cutting-brushing-2 | crew-management, corridor-clearing-power-tools | 5.3 | 8,623 | 6.3 |
| retrieval-10 | multi-hop | 3/3 | - | hand-built-trail-construction | 3.0 | 6,665 | 3.8 |

## dci

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 3/3 | - | - | 8.0 | 12,228 | 5.2 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×3, crew-management ×2 | - | 6.7 | 15,661 | 5.3 |
| retrieval-03 | multi-hop | 3/3 | - | - | 6.0 | 11,479 | 4.2 |
| retrieval-04 | multi-hop | 0/3 | hand-built-trail-construction ×3, jobsite-safety ×3 | - | 6.3 | 11,389 | 4.7 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 3.3 | 15,982 | 3.5 |
| retrieval-06 | multi-hop | 0/3 | tread-hardening ×3, mechanized-trail-construction | - | 5.0 | 9,818 | 3.7 |
| retrieval-07 | decline | 3/3 | - | - | 1.0 | 14,106 | 1.3 |
| retrieval-08 | decline | 3/3 | - | - | 1.0 | 14,106 | 1.3 |
| retrieval-09 | multi-hop | 2/3 | corridor-clearing-pruning-side-cutting-brushing-2, water-management-drainage-features-2 | crew-management ×3, crew-training ×2 | 6.3 | 26,482 | 4.6 |
| retrieval-10 | multi-hop | 3/3 | - | - | 3.0 | 3,029 | 2.1 |
