# TC3 question candidates from the Cairn knowledge base

**Superseded as the working question set on 2026-10-27:** the user requested
ten questions based on `golden.jsonl` instead. See [retrieval.jsonl](retrieval.jsonl)
and [the evaluation README](README.md). This source-backed candidate list is
retained for later stakeholder review; it is not the active labelled suite.

Collected 2026-10-26 from the local `flexion/flexion-cairn-kb` checkout at
commit `16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da`.

These ten candidates are grounded in existing project documents. Q1 and Q2
are verbatim questions in a sponsor-supplied requirements document. Q3–Q10
are assistant-written adaptations of documented needs and scenarios, not
verbatim user questions or evidence of an interview. The scenario specification
is a Flexion research proposal, not a validated sponsor-approved role library.

This is an intake list, **not the completed ten-question evaluation**. No gold
record IDs or pass/fail results have been assigned. The assignment asks for
real questions; the eight adaptations still need review against actual user
or stakeholder questions before being treated as satisfying that requirement.

## Candidates and origins

| ID | Question | Origin | Evidence |
| --- | --- | --- | --- |
| Q1 | How do I become a trail professional? | Verbatim sponsor-defined question | [src-0020, Emerging Trail Professional, 2.0 Goal][sponsor-goal] |
| Q2 | What should I learn next? | Verbatim sponsor-defined question | [src-0020, personalized recommendations][sponsor-next] |
| Q3 | Which skills does this role require, and at what levels? | Adapted from a documented scenario | [src-0024, UC-CE-A3, main flow 2–3][role] lists category-scoped competencies and expected levels. |
| Q4 | Which required skills do I already have, which am I close to, and which am I missing? | Adapted from a documented scenario | [src-0024, UC-CE-C2, main flow 1–4][gap] compares self-ratings to a selected role and presents has / close / missing. |
| Q5 | Which training would help me close this skill gap? | Adapted from a documented scenario | [src-0024, UC-CE-C2, main flow 5][routes] calls for a concrete route for each gap, including catalog training. |
| Q6 | Is there a free training option for my next step? | Adapted from documented guidance | [src-0024, UC-CE-C1, notes][free] requires prominent free and employer-paid options. |
| Q7 | How much does this training cost? | Adapted from a documented scenario | [src-0024, UC-CE-C3, main flow 3 and notes][cost] requires cost-aware recommendations with the cost shown. |
| Q8 | What would completing this training prove? | Adapted from a documented scenario | [src-0024, UC-CE-C3, main flow 4][proof] requires the recommendation to state what completion proves. |
| Q9 | Why are you recommending this training for me? | Adapted from a documented scenario | [src-0024, UC-CE-C3, main flow 1–2][reason] connects the explanation to the current profile, desired role, and gaps. |
| Q10 | Can I take this training online or somewhere near me? | Adapted from a sponsor requirement | [src-0020, personalized training recommendations][availability] explicitly requests online and geographic filters. |

## What is needed to label them

Question provenance and answer provenance are different. The documents above
explain **why the question matters**; they are not gold records proving that
a particular course or role in the TC2 dataset is real or correct.

| Candidates | Required context and evidence | Current readiness |
| --- | --- | --- |
| Q1 | Career goal plus verified role entry routes, requirements, and available opportunities | Broader than the current gap-and-next-step MVP. Preserve as a discovery question; narrow it with the user or replace it for the scored set. TC2 records cannot substantiate a complete career pathway. |
| Q2 | Selected target role, current self-ratings, role requirements, and training catalog slice | Candidate for a combined retrieval-and-computation case after a specific scenario is identified. |
| Q3 | A selected role definition, including its category-scoped required skills and levels | Candidate role lookup. A role name alone is ambiguous for the four repeated names listed in the data review. |
| Q4 | Selected role requirements plus the user's self-ratings | Retrieve requirements and compute the gaps. Self-ratings are request context, not evidence to retrieve from another person's scenario. |
| Q5 | A named gap with category and required level, and relevant training alignments | Candidate training-selection case. Preserve approval state and category scoping. |
| Q6 | The user's gap and the complete catalog slice for the selected scenario, including prices and alignments | A free course somewhere in the dataset is not automatically relevant. There is only one zero-cost training record in the recovered dataset; check its scenario before selecting a label. A no-match answer must be scoped to the available catalog. |
| Q7 | An identified training's `cost_usd` | Candidate lookup of a fictional course price. It is not evidence of a current real-world price. |
| Q8 | An identified training's `proves` field | Candidate lookup. Describe the recorded completion evidence without upgrading it to verified competency or an accredited credential. |
| Q9 | Current profile, selected role requirement, selected training's alignment/level and cost | Candidate multi-record explanation. Derive the reason from the input facts; never retrieve the synthetic `output` or `why`. |
| Q10 | An identified training, the user's location, and reliable delivery-mode/location information | Candidate decline case for the current corpus. Training records contain no location or delivery-mode fields. The title “Remote Bridge Checkup Day” does not establish online availability. Do not invent a nearby offering. |

All role and training facts in the recovered dataset remain synthetic. All
35 profiles still trigger the app's framework validation because their required
skill names are outside its governed vocabulary. Selecting gold records does
not resolve that integration blocker. See [TC3_DATA_REVIEW.md](../TC3_DATA_REVIEW.md).

## Turning candidates into the evaluation

1. Review the adapted wording against real questions or confirm its source
   with a stakeholder. Retain the distinction between a quote and an adaptation.
2. Supply explicit context for “this role,” “this training,” “my gap,” and “me.”
   If a synthetic fixture is used, identify it as such and preserve the original
   source question alongside the adapted test case.
3. Identify every supporting record using `data/retrieval_manifest.json` and
   `data/retrieval_sources.jsonl`. Keep each fictional profile's facts together;
   do not join conflicting role definitions merely because names match.
4. Review the expected answer and required citations, then assign `lookup`,
   `multi-hop`, or `decline` and write the final `retrieval.jsonl`.
5. Record how many finalized cases need multiple source records. That count
   is not yet known; neither a technique nor a top-k value has been chosen.

An unlabelled question is not a decline case. Do not use an empty `gold` list
as a placeholder for unfinished labels. Q10 is a candidate decline specifically
because the requested availability evidence is absent, not because labelling
has not been done.

## Source trail

- **src-0020:** [wiki source summary][sponsor-summary] → original
  `_sources/docs/trailskills-2-0-user-profiles-goals.md`. Sponsor-supplied
  document, shared by PTBA; author and document date are unconfirmed.
- **src-0024:** [wiki source summary][scenarios-summary] → original
  `_sources/docs/career-exploration-scenarios.md`. Flexion-internal research
  specification, last reviewed 2026-08-13. It expands the sponsor requirements
  into proposed scenarios; those scenarios are not interview transcripts.

[sponsor-goal]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/trailskills-2-0-user-profiles-goals.md#L44
[sponsor-next]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/trailskills-2-0-user-profiles-goals.md#L55
[role]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L389
[gap]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L734
[routes]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L745
[free]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L715
[cost]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L801
[proof]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L786
[reason]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/career-exploration-scenarios.md#L780
[availability]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/_sources/docs/trailskills-2-0-user-profiles-goals.md#L60
[sponsor-summary]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/wiki/sources/src-0020.md
[scenarios-summary]: https://github.com/flexion/flexion-cairn-kb/blob/16bba3cd1ab63da5bb3562f8e2a76ed7d5a0d1da/wiki/sources/src-0024.md
