# TC3 retrieval comparison

Run: 2026-10-27 19:45 · model: openai/bedrock/gpt-5.6-luna via https://llm.cloud.flexion.us/openai/v1 · UNSCOPED (ranked over every scope) · 10 questions

| technique | pass | cited | recall | mean calls | mean evidence chars | mean latency s | stopped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| lookup | 9/10 | 6/8 | 8/8 | 1.0 | 4262.4 | 1.9 | answer 10 |
| bm25_rag | 9/10 | 7/8 | 8/8 | 2.3 | 9897.1 | 2.8 | answer 10 |
| dci_wiki | 8/10 | 5/8 | 6/8 | 4.2 | 11573.0 | 2.9 | answer 10 |
| dense | 8/10 | 5/8 | 7/8 | 2.0 | 4191.3 | 2.2 | answer 10 |
| hybrid | 9/10 | 5/8 | 7/8 | 2.0 | 5606.1 | 2.5 | answer 10 |

Per question (✓ pass · ✗ fail · · not applicable):

| question | kind | lookup | bm25_rag | dci_wiki | dense | hybrid |
| --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | lookup | pass ✓ cite ✓ recall ✓ · 1 calls · 3207 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 15843 ch | pass ✗ cite ✗ recall ✗ · 1 calls · 2593 ch | pass ✓ cite ✗ recall ✓ · 2 calls · 3437 ch | pass ✓ cite ✗ recall ✓ · 2 calls · 5477 ch |
| retrieval-02 | lookup | pass ✓ cite ✗ recall ✓ · 1 calls · 4042 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 19206 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 12306 ch | pass ✗ cite ✓ recall ✓ · 2 calls · 3570 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 6640 ch |
| retrieval-03 | multi-hop | pass ✓ cite ✗ recall ✓ · 1 calls · 5877 ch | pass ✓ cite ✗ recall ✓ · 3 calls · 8078 ch | pass ✓ cite ✗ recall ✓ · 6 calls · 12402 ch | pass ✓ cite ✗ recall ✗ · 2 calls · 4822 ch | pass ✓ cite ✗ recall ✗ · 2 calls · 7016 ch |
| retrieval-04 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 5033 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 10561 ch | pass ✓ cite ✓ recall ✓ · 4 calls · 8164 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 2766 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 6720 ch |
| retrieval-05 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 7196 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 782 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1575 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1592 ch |
| retrieval-06 | lookup | pass ✓ cite ✓ recall ✓ · 1 calls · 7692 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 8576 ch | pass ✓ cite ✓ recall ✓ · 7 calls · 34494 ch | pass ✓ cite ✗ recall ✓ · 2 calls · 9162 ch | pass ✓ cite ✗ recall ✓ · 2 calls · 12312 ch |
| retrieval-07 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 5682 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 5860 ch | pass ✓ cite ✓ recall ✓ · 9 calls · 18976 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 4202 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 2084 ch |
| retrieval-08 | decline | pass ✗ cite · recall · · 1 calls · 5565 ch | pass ✗ cite · recall · · 1 calls · 4092 ch | pass ✗ cite · recall · · 3 calls · 10097 ch | pass ✗ cite · recall · · 2 calls · 6078 ch | pass ✗ cite · recall · · 2 calls · 6223 ch |
| retrieval-09 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 3821 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 13222 ch | pass ✓ cite ✗ recall ✗ · 5 calls · 12224 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 4438 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 6058 ch |
| retrieval-10 | decline | pass ✓ cite · recall · · 1 calls · 686 ch | pass ✓ cite · recall · · 2 calls · 6337 ch | pass ✓ cite · recall · · 2 calls · 3692 ch | pass ✓ cite · recall · · 2 calls · 1863 ch | pass ✓ cite · recall · · 2 calls · 1939 ch |

## Settings

- Model: openai/bedrock/gpt-5.6-luna via https://llm.cloud.flexion.us/openai/v1; temperature as the provider defaults; answer timeout 60 s
- Turn budget for the agent loops: 6; top-k for the single-shot techniques: 4
- Chunking: none. One chunk per record, rendered by `corpus.render` (the record's own boundary)
- Corpus per scope: ALL=136 records
- Embedding model: BAAI/bge-small-en-v1.5 (local); RRF k=60
- Embedding tokens: n/a (local ONNX model, no token accounting)
- Scoring: `expected_terms` / `must_not` in retrieval.jsonl; cited = every gold id appears in square brackets in the answer; recall = every gold id was retrieved before the answer call
- Raw answers and traces: `retrieval_results_unscoped.jsonl`
