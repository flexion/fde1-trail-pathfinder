# AI-1 retrieval results (step 1: find skills)

Technique: BM25 (rank_bm25 BM25Okapi) over 55 wiki pages, whole page per document. Decline when the top score < 8.0.

| id | kind | top score | recall@5 | recall@8 | recall@12 | gold ranks | ms |
| --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | 22.5 | 3/4, 2 wrong | 3/4, 5 wrong | 3/4, 9 wrong | corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 1, water-management-drainage-features-2: 3, hand-built-trail-construction: 5, corridor-clearing-pruning-side-cutting-brushing-2: 14 | 0.5 |
| retrieval-02 | multi-hop | 12.0 | 2/4, 3 wrong | 3/4, 5 wrong | 3/4, 9 wrong | jobsite-safety: 1, crew-management: 4, corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut: 7, corridor-clearing-felling-tree-removal-chainsaw-crosscut: 40 | 0.2 |
| retrieval-03 | multi-hop | 18.1 | 2/4, 3 wrong | 4/4, 4 wrong | 4/4, 8 wrong | retaining-walls: 1, mechanized-trail-construction: 3, water-management-drainage-features: 6, water-management-drainage-features-2: 7 | 0.3 |
| retrieval-04 | multi-hop | 25.2 | 2/5, 3 wrong | 4/5, 4 wrong | 4/5, 8 wrong | retaining-walls: 1, crew-training: 2, crew-management: 6, jobsite-safety: 7, hand-built-trail-construction: 47 | 0.3 |
| retrieval-05 | lookup | 10.8 | 1/1, 4 wrong | 1/1, 7 wrong | 1/1, 11 wrong | tread-maintenance-hand-tools: 4 | 0.2 |
| retrieval-06 | multi-hop | 16.5 | 3/5, 2 wrong | 3/5, 5 wrong | 4/5, 8 wrong | retaining-walls: 1, water-management-drainage-features-2: 4, water-management-drainage-features: 5, mechanized-trail-construction: 9, tread-hardening: 26 | 0.3 |
| retrieval-07 | decline | 3.3 | pass | pass | pass | - | 0.1 |
| retrieval-08 | decline | 6.3 | pass | pass | pass | - | 0.2 |

- k=5: all gold found in 1/6 answerable; declines correct 2/2
- k=8: all gold found in 2/6 answerable; declines correct 2/2
- k=12: all gold found in 2/6 answerable; declines correct 2/2
