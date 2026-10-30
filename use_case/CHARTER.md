# Project charter

<!--
  Filled in during TC1. Later weeks' notebooks read this file and stop if it
  is still the template. Amended as the cohort goes.
-->

**Department:** Flexion, TrailSkills 2.0 Career Exploration team (delivery partner to American Trails and PTBA)

**Working title:** Trail Pathfinder: gap and next step

---

## The problem

**Who has it?** One real role, not a department.

A second-season conservation corps member, a few weeks from the end of her
season with nothing lined up. No trail-specific credential, phone-only, poor
signal at the work site, explores in the evening. (The product persona calls
her Maya.)

**What are they trying to do?**

Find out which of the skills a real trail job requires she already has, which
she is close to, and the one thing she should do next. She wants one concrete
next action, not a menu of twelve, and free options first.

**How do they handle it today?**

- Self-assess on TrailSkills 1.0, where people rate themselves expert at
  everything and the result is not useful.
- Browse the skills library on her own. There is no guided pathway.
- Read job postings that name credentials she has never heard of and cannot
  price.
- Ask a supervisor, whose memory is the only record of what she can do.

**What does that cost — time, money, risk, or relationships?**

Unknown in hours or dollars; asking the product owner. The one sourced
indicator: of roughly 1,600 TrailSkills.org members, 300 to 400 have made a
profile and about 18 are any good, by the platform owner's own estimate. The
process fails for nearly everyone who tries. The named risk is that she gets
pushed toward unnecessary paid training.

**The problem in one sentence. No solution in it.**

A corps member nearing the end of her season has no way to see her skills
against a real trail job, so she guesses what she is missing and what to learn
next.

---

## Success

**What does the new world look like for that person?**

In about ten minutes, signed out, on her phone, she picks a role, rates
herself on the skills it actually requires, and leaves with her strengths
first, her gaps named, and one next step she can afford, with the reason
shown. Nothing is recorded on her behalf.

**How would the firm measure it? Which numbers should move?**

- Primary: share of comparisons that end with one next step accepted.
- Secondary: correction rate on suggested next steps (how often she edits or
  rejects one), reviewed in aggregate with the framework stewards.
- Gate, not a metric: every reason traces to a named skill and a catalog
  training. Anything that does not is discarded.

---

## The first product

**Your solution in one sentence.**

*Amended 2026-10-29 (Week 3), after the product owner meeting of 2026-10-28:*
Given what she has done, in her own words, suggest which framework competencies
she likely has and at what level, each with a reason she can check; and given a
description of her current job, name the one to three library roles closest to
it. The gap and next step below are the step after that, and are unchanged.

*Original (TC1):* Given a target role and her self-rated level on each of its
required skills, return the gap ordered has, close, missing, and up to three
next steps, each tied to one gap, naming a catalog training with its cost, what
it proves, and a one-line reason.

**Input → Output.** Be specific enough that someone could build it wrong and you
would notice.

| | |
| --- | --- |
| **In (AI-1)** | Zero or more backgrounds she picks from a short list (corps, military, landscaping, construction trades, forestry or wildland fire, trail volunteering) plus free text in her own words. Either may be empty, not both. |
| **Out (AI-1)** | At most **12** competencies from the framework's 55, each with its category, a level (Entry, Full Performance, Expert), a confidence (**likely**, **possible**, **check**) and a one-line reason that quotes her words or names the background. Likely and possible are pre-checked; she confirms every one, and nothing is recorded until she does. An id not in the framework never reaches the screen. Expert is never suggested unless she said it. Text that names no task, tool or feature gets a decline that asks for more, not a guess. |
| **In (AI-2)** | A description of her current job, or a pasted job posting. |
| **Out (AI-2)** | The **1 to 3** closest of the 12 library roles, in order, each with a one-line reason drawn from the role profile. Then the rules load that role's competencies and levels from the golden mapping for her to keep or remove. A job the library has nothing close to gets "The role library doesn't cover that yet", pointing at the nearest competency it does have. |
| **In (AI-4, unchanged)** | A target role (one of the 12 library roles), plus her level on each skill that role requires: Entry, Full Performance, Expert, or none. |
| **Out (AI-4, unchanged)** | The role's required skills grouped **has**, **close**, **missing**, in that order, each showing the required level and her level. Then at most **3** next steps, ranked, each tied to exactly one close or missing skill, naming a training from the catalog, its cost, what it proves, and a one-line reason. A skill with no catalog training says so instead of inventing one. No percentages anywhere. Nothing is saved as a claim. |

Constraints the output must respect (from the TrailSkills business rules):
skills stay scoped to their category; framework text and course details are
retrieved and cited, never generated; an agent-proposed training alignment is
a labeled draft until a steward approves it.

---

## Decisions made later

<!--
  Amended as the cohort goes. Keep the reasoning, not just the choice — Week 5
  asks you to defend your architecture against the options you rejected, and
  Week 10's handoff doc is largely this section.
-->

| Week | Decision | Why, and what you rejected |
| --- | --- | --- |
| 1 | Cap next steps at 3 total, ranked, not one per gap | BR-6.5 is a tested business rule; the Pathfinder proposal's "one per gap" is a proposal, and the proposals README says the repo wins where they disagree |
| 1 | User is the emerging professional (corps member), not the working crew leader | The crew leader's gap view needs the evidenced/unevidenced split, which depends on the credential wallet this app cannot reach |
| 3 | Direct SQL lookup over the stored role library and catalog, by exact name within a scope; no ranking. Measured against BM25 Agentic RAG, a model-navigated wiki, dense and hybrid retrieval. | See `use_case/decisions.md` Week 3: exact answers want exact queries; ranking only adds a way to be wrong. The schema gained `sources`; requirements and catalog are now looked up, not passed in. |
| 3 | **Scope pivot (2026-10-28): the first product is AI-1 and AI-2 of the client's AI integration spec, not the gap.** Goldens rebuilt from the 12 golden role profiles and the competency map; the TC1 gap goldens kept as `golden-gap.jsonl`. | The product owner and project lead showed the prototype to the partners on 2026-10-28 and then scoped our work to the two P1 features the prototype fakes: free text to competencies, job text to closest role. We rejected keeping gap-first and bolting the new features on, because the gap is the step after a profile exists and the prototype already does it by rules. The input is now free text, so the "no retrieval" decision is reopened (`decisions.md`). |
| 5 | Agent architecture | <!-- TC5 --> |
| 8 | Model | <!-- TC8 --> |
