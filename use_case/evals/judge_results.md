# Judge check (Week 4 Step 3)

Judge model: `openai/bedrock/claude-sonnet-5-5` (the endpoint answers with `openai/bedrock/gpt-5.6-luna`). Rubric: `JUDGE_RUBRIC` in `harness.py`, for failures.md lines 5 and 6 under the easy rule.

## Separation (13 AI-1 goldens)

| answer | judge mean |
| --- | --- |
| golden output (known good) | 1.00 |
| unrelated pre-checked skills (known bad) | 0.08 |
| echo of her input (known bad) | 0.00 |

`helpers.judge`: **USABLE: accepted 1.00 (want >0.8), wrong 0.08 (want <0.3), separation 0.92, n=13**

## Agreement (20 hand scores)

Human: 12 pass, 8 fail. Chance floor (always guess the more common verdict): 0.60.

| | agreement |
| --- | --- |
| judge alone | 0.90 |
| judge + `decline_wording` (how a trace is scored) | 0.95 |

| id | human | judge | judge + decline_wording |
| --- | --- | --- | --- |
| t-ai1-04 | pass | pass | pass |
| t-gen-26 | fail | fail | fail |
| t-ai1-06 | pass | pass | pass |
| t-gen-32 | fail | fail | fail |
| t-ai1-13 | pass | pass | pass |
| t-gen-23 | pass | pass | pass |
| t-gen-25 | fail | fail | fail |
| t-ai1-14 | pass | pass | pass |
| t-ai1-03 | pass | pass | pass |
| t-gen-30 | fail | pass | fail |
| t-gen-31 | pass | pass | fail ⚠️ |
| t-gen-20 | pass | pass | pass |
| t-gen-10 | fail | fail | fail |
| t-gen-13 | pass | pass | pass |
| t-ai1-12 | pass | pass | pass |
| t-gen-37 | fail | pass | fail |
| t-gen-28 | pass | pass | pass |
| t-gen-08 | fail | fail | fail |
| t-ai1-07 | pass | pass | pass |
| t-gen-12 | fail | fail | fail |

Judge calls: 59, 61,640 prompt + 18,217 completion tokens, 202 s (measured).
