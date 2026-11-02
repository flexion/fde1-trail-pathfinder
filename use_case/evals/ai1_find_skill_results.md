# AI-1 retrieval results (step 1: find skills, no model)

55 wiki pages, one document per page. `retrieval.jsonl`: 10 questions. Decline when the top page scores below the technique's threshold. Twins (the same skill under two categories) count as one gold skill: either passes.

| technique | decline below | k | all gold found | gold recall | declines correct | avg ms |
| --- | --- | --- | --- | --- | --- | --- |
| bm25 | 8.0 | 5 | 1/8 | 61% | 2/2 | 0.3 |
| bm25 | 8.0 | 8 | 4/8 | 79% | 2/2 | 0.3 |
| bm25 | 8.0 | 12 | 5/8 | 86% | 2/2 | 0.3 |
| dense | 0.2 | 5 | 1/8 | 57% | 1/2 | 877.4 |
| dense | 0.2 | 8 | 2/8 | 71% | 1/2 | 877.4 |
| dense | 0.2 | 12 | 4/8 | 82% | 1/2 | 877.4 |

## bm25

| id | kind | top score | recall@5 | recall@8 | recall@12 | gold ranks | ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 22.51 | 3/4, 0 wrong | 3/4, 3 wrong | 4/4, 6 wrong | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 1, water-management-drainage-features-2: 3, hand-built-trail-construction: 5, corridor-clearing-pruning-side-cutting-brushing-2: 12 | 0.4 |
| retrieval-02 | multi-hop | 11.95 | 2/3, 3 wrong | 3/3, 5 wrong | 3/3, 9 wrong | jobsite-safety: 1, crew-management: 4, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut / corridor-clearing-felling-tree-removal-chainsaw-crosscut: 7 | 0.3 |
| retrieval-03 | multi-hop | 18.12 | 2/3, 3 wrong | 3/3, 4 wrong | 3/3, 8 wrong | retaining-walls: 1, mechanized-trail-construction: 3, water-management-drainage-features / water-management-drainage-features-2: 6 | 0.2 |
| retrieval-04 | multi-hop | 25.22 | 2/5, 3 wrong | 4/5, 4 wrong | 4/5, 8 wrong | retaining-walls: 1, crew-training: 2, crew-management: 6, jobsite-safety: 7, hand-built-trail-construction: 47 | 0.4 |
| retrieval-05 | lookup | 10.81 | 1/1, 4 wrong | 1/1, 7 wrong | 1/1, 11 wrong | tread-maintenance-hand-tools: 4 | 0.2 |
| retrieval-06 | multi-hop | 16.53 | 2/4, 2 wrong | 2/4, 5 wrong | 3/4, 8 wrong | retaining-walls: 1, water-management-drainage-features / water-management-drainage-features-2: 4, mechanized-trail-construction: 9, tread-hardening: 26 | 0.2 |
| retrieval-07 | decline | 3.31 | pass | pass | pass | - | 0.0 |
| retrieval-08 | decline | 6.29 | pass | pass | pass | - | 0.2 |
| retrieval-09 | multi-hop | 29.67 | 3/5, 2 wrong | 3/5, 5 wrong | 3/5, 9 wrong | funding-grants: 1, communications: 4, education-and-public-outreach: 5, water-management-drainage-features-2: 21, corridor-clearing-pruning-side-cutting-brushing-2: 40 | 0.5 |
| retrieval-10 | multi-hop | 27.94 | 2/3, 3 wrong | 3/3, 5 wrong | 3/3, 8 wrong | tread-maintenance-hand-tools: 3, water-crossing-structures-boardwalk-puncheon-turnpike-ford: 4, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 8 | 0.3 |

## dense

| id | kind | top score | recall@5 | recall@8 | recall@12 | gold ranks | ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 0.46 | 2/4, 1 wrong | 2/4, 4 wrong | 2/4, 8 wrong | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 1, corridor-clearing-pruning-side-cutting-brushing-2: 4, hand-built-trail-construction: 13, water-management-drainage-features-2: 20 | 0.1 |
| retrieval-02 | multi-hop | 0.34 | 2/3, 2 wrong | 3/3, 4 wrong | 3/3, 8 wrong | crew-management: 1, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut / corridor-clearing-felling-tree-removal-chainsaw-crosscut: 3, jobsite-safety: 6 | 0.0 |
| retrieval-03 | multi-hop | 0.31 | 2/3, 2 wrong | 2/3, 5 wrong | 3/3, 8 wrong | retaining-walls: 1, water-management-drainage-features / water-management-drainage-features-2: 2, mechanized-trail-construction: 9 | 0.0 |
| retrieval-04 | multi-hop | 0.51 | 3/5, 2 wrong | 3/5, 5 wrong | 4/5, 8 wrong | crew-training: 1, hand-built-trail-construction: 2, crew-management: 3, retaining-walls: 12, jobsite-safety: 31 | 0.0 |
| retrieval-05 | lookup | 0.40 | 1/1, 4 wrong | 1/1, 7 wrong | 1/1, 11 wrong | tread-maintenance-hand-tools: 1 | 0.0 |
| retrieval-06 | multi-hop | 0.33 | 2/4, 2 wrong | 3/4, 4 wrong | 3/4, 8 wrong | retaining-walls: 1, water-management-drainage-features / water-management-drainage-features-2: 2, tread-hardening: 7, mechanized-trail-construction: 14 | 0.0 |
| retrieval-07 | decline | 0.46 | fail | fail | fail | - | 0.0 |
| retrieval-08 | decline | 0.11 | pass | pass | pass | - | 0.0 |
| retrieval-09 | multi-hop | 0.45 | 3/5, 2 wrong | 4/5, 4 wrong | 4/5, 8 wrong | funding-grants: 1, education-and-public-outreach: 2, communications: 3, water-management-drainage-features-2: 8, corridor-clearing-pruning-side-cutting-brushing-2: 26 | 8450.7 |
| retrieval-10 | multi-hop | 0.44 | 1/3, 4 wrong | 2/3, 6 wrong | 3/3, 9 wrong | tread-maintenance-hand-tools: 3, water-crossing-structures-boardwalk-puncheon-turnpike-ford: 8, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 10 | 323.1 |
