# TC5: the tool loop capped at 4 searches vs the skill

Measured 2026-11-23 by `ways_compare.py --cap 4`, same requests, model and k as Step 4 in `ways_results.md`. The tool loop's `find_skills` stops searching after 4 calls (`max_searches`; past it the model is told to answer), matching the skill's `MAX_SEARCHES = 4` plan. Median of the runs, range in brackets.

Searches run counts only calls that reached `search_chunks`. The token split: **fixed prompt** is turn 1's prompt (system prompt + her text + chips); **fixed re-sent** is that prompt again on every later model call; **search added** is how much each later prompt grew beyond the previous one plus its completion, i.e. the search results; **per search** divides that by the searches run. For the skill, the answer call has its own system prompt (the policy), so its search added also carries the difference between the plan and answer prompts: read it as an upper bound.

| way | request | searches run | model calls | tokens | fixed prompt | fixed re-sent | search added | per search | completion | latency ms | errors |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| tool | t-ai1-01 | 4 | 2 (2–3) | 3536 (3507–5553) | 499 | 499 (499–998) | 1452 (1221–1466) | 363 (305–366) | 886 (877–1276) | 4995 (4447–10421) | 0/3 |
| skill | t-ai1-01 | 3 (1–4) | 2 | 3484 (2411–3582) | 306 | 306 | 1423 (735–1572) | 474 (393–735) | 1194 (952–1416) | 15061 (7180–16641) | 0/3 |
| tool | t-ai1-13 | 4 | 3 | 3910 (3818–4295) | 371 | 742 | 989 (873–993) | 247 (218–248) | 661 (543–690) | 6023 (5687–6043) | 0/3 |
| skill | t-ai1-13 | 1 | 2 | 1557 (1497–1592) | 178 | 178 | 756 (713–758) | 756 (713–758) | 362 (345–443) | 5358 (5155–6055) | 0/3 |

## Per run

| way | request | run | searches | per-turn prompt / completion / tool calls |
| --- | --- | --- | --- | --- |
| tool | t-ai1-01 | 1 | 4 | 499/144/4; 1784/130/4; 1994/1002/0 |
| tool | t-ai1-01 | 2 | 4 | 499/180/5; 2131/697/0 |
| tool | t-ai1-01 | 3 | 4 | 499/186/5; 2151/700/0 |
| skill | t-ai1-01 | 1 | 1 | 306/112/1; 1153/840/0 |
| skill | t-ai1-01 | 2 | 3 | 306/131/1; 1860/1285/0 |
| skill | t-ai1-01 | 3 | 4 | 306/106/1; 1984/1088/0 |
| tool | t-ai1-13 | 1 | 4 | 371/128/4; 1509/262/5; 1754/271/0 |
| tool | t-ai1-13 | 2 | 4 | 371/115/3; 1292/137/1; 1612/291/0 |
| tool | t-ai1-13 | 3 | 4 | 371/103/3; 1255/247/1; 1594/340/0 |
| skill | t-ai1-13 | 1 | 1 | 178/38/1; 974/307/0 |
| skill | t-ai1-13 | 2 | 1 | 178/83/1; 1017/279/0 |
| skill | t-ai1-13 | 3 | 1 | 178/80/1; 971/363/0 |
