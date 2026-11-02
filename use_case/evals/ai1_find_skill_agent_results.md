# AI-1 step 1, Agentic RAG (search_chunks + model)

Model: `openai/bedrock/gpt-5.6-luna`. 220 chunks from 55 wiki pages (split at `##`). Max 6 turns, k capped at 8. One run per case. Twins (the same skill under two categories) count as one gold skill: either passes.

| technique | all gold found | gold recall | wrong named | declines correct | quotes ok | avg calls | avg evidence chars | avg s |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bm25 | 2/6 | 75% | 1 | 2/2 | 16/16 | 3.4 | 5,425 | 2.9 |
| dense | 4/6 | 90% | 0 | 2/2 | 18/18 | 3.2 | 6,959 | 4.3 |

## bm25

| id | kind | pass | found | missed | wrong | quotes ok | calls | evidence chars | s | stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | pass | 4/4 | - | - | 4/4 | 4 | 5,673 | 3.4 | answer |
| retrieval-02 | multi-hop | FAIL | 2/3 | jobsite-safety | - | 2/2 | 4 | 5,732 | 3.8 | answer |
| retrieval-03 | multi-hop | pass | 3/3 | - | - | 3/3 | 4 | 6,797 | 3.0 | answer |
| retrieval-04 | multi-hop | FAIL | 3/5 | hand-built-trail-construction, jobsite-safety | - | 3/3 | 5 | 7,830 | 3.5 | answer |
| retrieval-05 | lookup | FAIL | 0/1 | tread-maintenance-hand-tools | maintenance-specifications | 1/1 | 4 | 5,347 | 3.0 | answer |
| retrieval-06 | multi-hop | FAIL | 3/4 | tread-hardening | - | 3/3 | 4 | 7,164 | 3.8 | answer |
| retrieval-07 | decline | pass | 0/0 | - | - | 0/0 | 1 | 1,865 | 1.7 | answer |
| retrieval-08 | decline | pass | 0/0 | - | - | 0/0 | 1 | 2,990 | 1.4 | answer |

## dense

| id | kind | pass | found | missed | wrong | quotes ok | calls | evidence chars | s | stopped |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | multi-hop | pass | 4/4 | - | - | 4/4 | 4 | 11,575 | 4.6 | answer |
| retrieval-02 | multi-hop | FAIL | 2/3 | jobsite-safety | - | 2/2 | 4 | 7,061 | 6.1 | answer |
| retrieval-03 | multi-hop | pass | 3/3 | - | - | 3/3 | 3 | 5,646 | 4.0 | answer |
| retrieval-04 | multi-hop | FAIL | 4/5 | jobsite-safety | - | 4/4 | 6 | 9,399 | 5.9 | answer |
| retrieval-05 | lookup | pass | 1/1 | - | - | 1/1 | 3 | 8,982 | 3.8 | answer |
| retrieval-06 | multi-hop | pass | 4/4 | - | - | 4/4 | 4 | 6,509 | 6.7 | answer |
| retrieval-07 | decline | pass | 0/0 | - | - | 0/0 | 1 | 3,448 | 2.0 | answer |
| retrieval-08 | decline | pass | 0/0 | - | - | 0/0 | 1 | 3,054 | 1.7 | answer |
