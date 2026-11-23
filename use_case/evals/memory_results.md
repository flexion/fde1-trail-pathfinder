# TC7: procedural memory, tested directly

Measured 2026-11-23 by `memory_eval.py`, 3 pair(s) per request, each pair on an empty store, tool way, `LLM_MODEL` from `.env`. Median of the pairs, range in brackets.

## Offline (no model, no wiki; `run.py` runs these too)

| test | result |
| --- | --- |
| staleness | PASS |
| leakage | PASS |

## Recall at 10, 100 and 1,000 entries

| live entries | rows (incl. superseded) | recall | ms per recall |
| --- | --- | --- | --- |
| 10 | 30 | 1.00 | 0.005 |
| 100 | 300 | 1.00 | 0.003 |
| 1000 | 3000 | 1.00 | 0.003 |

The store is an exact lookup on an indexed key, not a search, so it cannot rank the wrong entry first and recall stays 1.00 as it grows. FTS is not used and is not needed. Where recall can go wrong is the key itself: `subject_of` picks the skill the wiki index ranks first for a sentence, and two wordings of the same work can land on different subjects (a miss, not a wrong entry). That is what the cost table below measures in practice.


## Cost: attempt one vs attempt two

| request | tokens 1 → 2 | searches 1 → 2 | model calls 1 → 2 | latency ms 1 → 2 | cheaper? |
| --- | --- | --- | --- | --- | --- |
| t-ai1-01 | 6796 (6747–10122) → 4478 (4141–7747) | 8 → 4 (4–5) | 3 → 2 (2–3) | 10232 (7666–13227) → 8096 (6550–10799) | yes |
| t-ai1-03 | 5609 (4829–9523) → 3795 (3226–6115) | 5 (4–6) → 3 (2–4) | 3 (3–4) → 2 (2–3) | 7576 (5274–9525) → 6182 (4355–6870) | yes |
| t-ai1-05 | 7031 (5855–11143) → 3715 (3542–5245) | 8 (7–10) → 1 (1–2) | 3 (3–4) → 2 (2–3) | 9242 (8963–11969) → 6012 (3719–6213) | yes |
| t-ai1-13 | 2505 (2056–4710) → 4234 (3620–4539) | 4 (3–6) → 3 (2–4) | 2 (2–3) → 2 (2–3) | 4097 (3704–7657) → 5071 (4649–11057) | **no** |

**Cost test: FAIL.** Median tokens over every pair: 6301 → 4187 (34% fewer).

## Truthfulness: the model's account vs the log (attempt two)

48 skill claims. The log supports **43**, contradicts **1**, and **4** gave no source. Truthfulness: **0.90**.

A contradiction is a skill the model said it matched in a remembered section when no remembered section was about that skill (or said it searched when no search returned it).

## Does memory make the answer worse? Text-path skills, attempt one vs two

| request | pair | attempt one | attempt two | lost on two | gained on two |
| --- | --- | --- | --- | --- | --- |
| t-ai1-01 | 1 | 4 | 4 | — | — |
| t-ai1-01 | 2 | 4 | 4 | — | — |
| t-ai1-01 | 3 | 4 | 4 | — | — |
| t-ai1-03 | 1 | 3 | 3 | — | — |
| t-ai1-03 | 2 | 2 | 3 | — | corridor-clearing-felling-tree-removal-chainsaw-crosscut |
| t-ai1-03 | 3 | 2 | 3 | — | crew-management |
| t-ai1-05 | 1 | 4 | 4 | — | — |
| t-ai1-05 | 2 | 5 | 4 | jobsite-safety | — |
| t-ai1-05 | 3 | 5 | 4 | jobsite-safety | — |
| t-ai1-13 | 1 | 5 | 5 | crew-management | corridor-clearing-pruning-side-cutting-brushing-2 |
| t-ai1-13 | 2 | 4 | 4 | — | — |
| t-ai1-13 | 3 | 4 | 4 | communications | crew-management |
