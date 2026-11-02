# AI-1 step 1, model + tools (Agentic RAG and DCI)

Model: `openai/bedrock/gpt-5.6-luna`. bm25/dense: 220 chunks from 55 wiki pages (split at `##`); dci: the 55 pages and the index. Max 6 turns, k capped at 8. **3 runs per case**: each cell is the mean, with the range across runs in brackets. Twins (the same skill under two categories) count as one gold skill: either passes.

| technique | all gold found (of 6) | gold recall | wrong named | declines correct (of 2) | quotes not in her text | calls | evidence chars | s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 2.7 (2.0–3.0) | 78% (75%–80%) | 1.3 (1.0–2.0) | 2.0 | 0.3 (0.0–1.0) | 3.7 (3.4–3.9) | 6,603 (5,903–7,088) | 3.3 (3.2–3.4) |
| dense | 2.7 (2.0–3.0) | 82% (80%–85%) | 1.0 | 2.0 | 0.0 | 3.4 (3.0–3.8) | 6,607 (6,137–7,322) | 4.5 (4.1–5.0) |
| dci | 2.3 (2.0–3.0) | 75% (70%–80%) | 1.3 (1.0–2.0) | 2.0 | 0.3 (0.0–1.0) | 4.5 (4.0–4.8) | 11,246 (9,486–13,051) | 3.6 (3.2–4.0) |

## bm25

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 2/3 | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut | corridor-clearing-bucking-felling-tree-removal-chainsaw-crosscut | 4.3 | 6,182 | 4.5 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×2, crew-management | - | 4.0 | 7,438 | 4.0 |
| retrieval-03 | multi-hop | 3/3 | - | - | 4.0 | 6,521 | 3.4 |
| retrieval-04 | multi-hop | 0/3 | hand-built-trail-construction ×3, jobsite-safety ×3 | - | 6.0 | 9,424 | 3.6 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 3.0 | 6,893 | 2.8 |
| retrieval-06 | multi-hop | 3/3 | - | - | 5.3 | 10,163 | 4.5 |
| retrieval-07 | decline | 3/3 | - | - | 1.0 | 2,723 | 1.5 |
| retrieval-08 | decline | 3/3 | - | - | 1.7 | 3,480 | 1.9 |

## dense

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 3/3 | - | - | 4.3 | 7,582 | 5.0 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×3 | - | 3.3 | 5,926 | 4.9 |
| retrieval-03 | multi-hop | 3/3 | - | - | 3.3 | 5,818 | 4.2 |
| retrieval-04 | multi-hop | 0/3 | jobsite-safety ×3, hand-built-trail-construction | - | 4.7 | 9,070 | 5.8 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 4.3 | 10,342 | 5.5 |
| retrieval-06 | multi-hop | 2/3 | mechanized-trail-construction | - | 4.0 | 6,658 | 5.1 |
| retrieval-07 | decline | 3/3 | - | - | 1.0 | 2,380 | 2.3 |
| retrieval-08 | decline | 3/3 | - | - | 2.3 | 5,080 | 3.3 |

## dci

| id | kind | passed | missed (times) | wrong (times) | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 3/3 | - | - | 6.7 | 9,373 | 3.9 |
| retrieval-02 | multi-hop | 0/3 | jobsite-safety ×3, crew-management | - | 6.0 | 11,423 | 4.8 |
| retrieval-03 | multi-hop | 3/3 | - | tread-hardening | 6.3 | 14,415 | 5.7 |
| retrieval-04 | multi-hop | 0/3 | jobsite-safety ×3, hand-built-trail-construction ×2 | - | 6.0 | 12,952 | 4.5 |
| retrieval-05 | lookup | 0/3 | tread-maintenance-hand-tools ×3 | maintenance-specifications ×3 | 3.7 | 16,767 | 3.5 |
| retrieval-06 | multi-hop | 1/3 | mechanized-trail-construction ×2, tread-hardening | - | 6.0 | 10,929 | 3.7 |
| retrieval-07 | decline | 3/3 | - | - | 1.0 | 14,106 | 1.7 |
| retrieval-08 | decline | 3/3 | - | - | 0.0 | 0 | 0.6 |
