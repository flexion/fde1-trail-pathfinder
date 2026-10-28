# TC3 retrieval comparison

Run: 2026-10-27 19:44 · model: openai/bedrock/gpt-5.6-luna via https://llm.cloud.flexion.us/openai/v1 · scoped (profile_id filter before ranking) · 10 questions

| technique | pass | cited | recall | mean calls | mean evidence chars | mean latency s | stopped |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| lookup | 10/10 | 8/8 | 8/8 | 0.9 | 885.4 | 1.4 | answer 9, declined_by_query 1 |
| bm25_rag | 10/10 | 8/8 | 8/8 | 2.1 | 1385.7 | 1.9 | answer 10 |
| dci_wiki | 10/10 | 8/8 | 8/8 | 3.2 | 865.3 | 2.4 | answer 10 |
| dense | 10/10 | 8/8 | 8/8 | 2.0 | 1226.4 | 1.7 | answer 10 |
| hybrid | 10/10 | 8/8 | 8/8 | 2.0 | 1226.4 | 1.6 | answer 10 |

Per question (✓ pass · ✗ fail · · not applicable):

| question | kind | lookup | bm25_rag | dci_wiki | dense | hybrid |
| --- | --- | --- | --- | --- | --- | --- |
| retrieval-01 | lookup | pass ✓ cite ✓ recall ✓ · 1 calls · 354 ch | pass ✓ cite ✓ recall ✓ · 1 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 530 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1019 ch |
| retrieval-02 | lookup | pass ✓ cite ✓ recall ✓ · 1 calls · 1189 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 2038 ch | pass ✓ cite ✓ recall ✓ · 4 calls · 1181 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch |
| retrieval-03 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 1521 ch | pass ✓ cite ✓ recall ✓ · 1 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 1232 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch |
| retrieval-04 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 1522 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 3057 ch | pass ✓ cite ✓ recall ✓ · 4 calls · 1502 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1854 ch |
| retrieval-05 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 1 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 4 calls · 958 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1019 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1019 ch |
| retrieval-06 | lookup | pass ✓ cite ✓ recall ✓ · 1 calls · 696 ch | pass ✓ cite ✓ recall ✓ · 1 calls · 534 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 638 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1007 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1007 ch |
| retrieval-07 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 1007 ch | pass ✓ cite ✓ recall ✓ · 1 calls · 534 ch | pass ✓ cite ✓ recall ✓ · 4 calls · 952 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1007 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 1007 ch |
| retrieval-08 | decline | pass ✓ cite · recall · · 0 calls · 0 ch | pass ✓ cite · recall · · 7 calls · 1869 ch | pass ✓ cite · recall · · 3 calls · 517 ch | pass ✓ cite · recall · · 2 calls · 771 ch | pass ✓ cite · recall · · 2 calls · 771 ch |
| retrieval-09 | multi-hop | pass ✓ cite ✓ recall ✓ · 1 calls · 860 ch | pass ✓ cite ✓ recall ✓ · 3 calls · 1749 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 576 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 860 ch | pass ✓ cite ✓ recall ✓ · 2 calls · 860 ch |
| retrieval-10 | decline | pass ✓ cite · recall · · 1 calls · 686 ch | pass ✓ cite · recall · · 1 calls · 1019 ch | pass ✓ cite · recall · · 3 calls · 567 ch | pass ✓ cite · recall · · 2 calls · 1019 ch | pass ✓ cite · recall · · 2 calls · 1019 ch |

## Settings

- Model: openai/bedrock/gpt-5.6-luna via https://llm.cloud.flexion.us/openai/v1; temperature as the provider defaults; answer timeout 60 s
- Turn budget for the agent loops: 6; top-k for the single-shot techniques: 4
- Chunking: none. One chunk per record, rendered by `corpus.render` (the record's own boundary)
- Corpus per scope: golden-01=3, golden-02=2, golden-03=1, golden-05=2 records
- Embedding model: BAAI/bge-small-en-v1.5 (local); RRF k=60
- Embedding tokens: n/a (local ONNX model, no token accounting)
- Scoring: `expected_terms` / `must_not` in retrieval.jsonl; cited = every gold id appears in square brackets in the answer; recall = every gold id was retrieved before the answer call
- Raw answers and traces: `retrieval_results.jsonl`
