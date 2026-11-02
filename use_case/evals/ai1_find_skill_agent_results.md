# AI-1 step 1, Agentic RAG (BM25 search_chunks + model)

Model: `openai/bedrock/gpt-5.6-luna`. 220 chunks from 55 wiki pages (split at `##`). Max 6 turns, k capped at 8.

| id | kind | pass | found | missed | wrong | quotes ok | calls | evidence chars | s | stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | pass | 4/4 | - | - | 4/4 | 4 | 5,673 | 4.2 | answer |
| retrieval-02 | multi-hop | FAIL | 2/4 | corridor-clearing-felling-tree-removal-chainsaw-crosscut, crew-management | - | 2/2 | 4 | 5,897 | 4.7 | answer |
| retrieval-03 | multi-hop | FAIL | 3/4 | water-management-drainage-features-2 | - | 3/3 | 7 | 9,347 | 4.4 | answer |
| retrieval-04 | multi-hop | FAIL | 3/5 | hand-built-trail-construction, jobsite-safety | - | 3/3 | 4 | 6,289 | 4.2 | answer |
| retrieval-05 | lookup | FAIL | 0/1 | tread-maintenance-hand-tools | maintenance-specifications | 1/1 | 2 | 5,456 | 2.5 | answer |
| retrieval-06 | multi-hop | FAIL | 3/5 | tread-hardening, water-management-drainage-features | - | 3/3 | 4 | 7,118 | 3.5 | answer |
| retrieval-07 | decline | pass | 0/0 | - | - | 0/0 | 1 | 3,126 | 1.4 | answer |
| retrieval-08 | decline | pass | 0/0 | - | - | 0/0 | 1 | 1,349 | 1.4 | answer |

- all gold found: 1/6 answerable
- declines correct: 2/2
- wrong skills named: 1; unknown ids: 0
