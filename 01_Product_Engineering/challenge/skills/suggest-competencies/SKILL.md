---
name: suggest-competencies
description: Find which trail skills a person's own words support, using the trailskills.org
  skills wiki. Use when someone describes work they have done, and maybe picks background
  chips, and wants it matched to trail competencies.
version: 1.0.0
---

# Suggest competencies

## When to use this
Someone has written, in her own words, about work she has done. She may also have picked
background chips (corps, forestry, landscaping, ...), each of which suggests some skills.

## How to use it
Run: `python run.py "<query>" [k]`

Run it once for each task, tool or trail feature she names, with her words as the query. It
prints the `k` best-matching skills-wiki chunks as JSON (default 4, at most 8). Search again
with different words when a task she names has no match yet. A page name is a skill id; a
chunk id is `<skill-id>#<section>`.

## Crediting policy

<!-- ^ This section is the point of the skill. It is policy, not code: it decides what we
     credit a person for, it changed twice in one week (2026-11-02 and 2026-11-03) from the
     product owner's feedback, and the person who owns it is a product manager, not an
     engineer. Edit it here; no code changes. -->

**What counts as evidence.** Use only the skills wiki. Name a skill only when her words
describe doing that work. Do not judge levels: every suggestion starts at Entry.

**Quote her exactly.** Every skill you name carries her exact words, copied from her text.
A quote that is not in her text is dropped, and its suggestion with it.

**Hedged words.** When her words hedge (only, a little, a few, some, helped, tried, watched,
took the, class), the suggestion is still shown but is not pre-checked: she decides. Keep the
hedge in the quote.

**When to decline.** If her text names no task, tool or trail feature, decline.

**Background chips.** You may also be given the skills her background chips suggest. Give
each one a verdict:

- `"supported"` when her words describe that work;
- `"points_away"` when her words say she did not do it, or describe what she did in that
  field and it is a different kind of work (a landscaping chip suggests Retaining Walls, but
  she writes that she only mowed and watered);
- `"silent"` when she just does not mention it. Silent is not points_away.

A chip skill her words point away from stays on her list but is not pre-checked.

<!-- Enforced in code as well, so editing these words alone does not change them: the
     exact-quote check, the hedge words (HEDGES in suggest.py), Entry for everything, and
     points_away needing a quote of hers. Code checks what the model says. -->

## Answer
Reply with JSON only:

```json
{"skills": [{"skill_id": "...", "quote": "her exact words"}],
 "chips": [{"skill_id": "...", "verdict": "supported|points_away|silent", "quote": "her words, or null"}],
 "declined": false, "reason": null}
```
