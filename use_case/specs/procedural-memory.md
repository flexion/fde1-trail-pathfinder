# Spec: AI-1 procedural memory

The checker is `uv run python use_case/evals/memory_eval.py`. A fresh agent given only
this file and the checker should be able to rebuild `procedures.py` and its hooks in
`suggest.py`; if the checker passes, the rebuild is acceptable.

## Goal

AI-1 works out from scratch, on every request, which sections of the skills wiki answer
the kind of work she describes. Remember which sections backed a credited skill last time,
hand them to the model up front, and let it search only for what they miss, so the same
kind of request costs less the second time without crediting different skills.

## Acceptance criteria (each one is a check in `memory_eval.py`)

| # | Criterion | Check |
| --- | --- | --- |
| A1 | One live entry per subject: a second write supersedes the first, and only the new value is recalled. | `test_staleness` |
| A2 | An entry learned against another wiki version is never recalled. | `test_staleness` |
| A3 | A stored row holds ids only: no 3-word run of her text reaches the store through the real write path, and a write of anything that is not a skill id or a wiki section id is refused. | `test_leakage` |
| A4 | Recall stays 1.00 at 10, 100 and 1,000 live entries. | `recall_at_scale` |
| A5 | On the same request twice from an empty store, attempt two uses fewer tokens and fewer searches (median over 3 pairs) for every request in `REQUESTS`. | cost table, `cheaper?` column |
| A6 | At least 0.90 of the model's per-skill source claims on attempt two ("remembered" or "searched") are supported by the log of what the store handed it and what each search returned. | truthfulness line |
| A7 | Attempt two does not lose a skill attempt one credited in a majority of pairs for any request. | "make the answer worse" table |

A1–A4 need no model and no wiki and run on every `run.py`. A5–A7 need the gateway and
the wiki.

## Constraints

- **Nothing she types is stored.** The page says "nothing you enter is saved". Model-written
  search queries are not stored either, because they copy her words.
- **Off by default.** It is on only when `SUGGEST_MEMORY` names a SQLite file. A store that
  cannot be opened or written leaves her answer unchanged.
- **Only checked skills teach it.** Write only from suggestions that passed the quote check
  and the evidence check (`suggest.backed`), so a poisoned wiki section cannot outlive its fix.
- **Remembered sections are wiki text, in a message of their own.** Never appended to her
  message: the quote check reads her message, and mixing the two made the model quote loosely.
- **SQLite, standard library.** No new dependency, no vector store.
- **The tool way only.** The skill way (`SUGGEST_WAY=skill`) is unchanged.

## Out of scope

Per-user memory (there are no users), remembering her answers or her rejected skills between
visits, and any change to what is credited: the evidence check and quote check are unchanged.
