# AI-1 failures: what goes wrong in fifty traces

*Written 2026-11-02 from the fifty traces in [traces.md](traces.md).*

**Source:** 50 runs of `suggest_competencies` (`traces.jsonl`):
- 13 AI-1 golden inputs;
- 34 inputs a model wrote across corps, fire, landscaping, veterans, volunteers, trades, office jobs, vague, off-topic and exaggerated answers;
- 3 chip-only inputs.

There are no real user traces yet, because AI-1 has not been in front of anyone. The generated inputs are checked against real people's words at the demo.

**41 of the 50 traces have at least one failure.** 27 of them overclaim: a pre-checked skill her words do not back (lines 1, 5 and 6). Five traces declined; four of those declines were right.

**The bar, from the twenty hand scores** (`human_scores.jsonl`, 8 fail): a `likely` skill is pre-checked on screen, so it must be backed by her words. A skill she described but the output missed is not a fail, because she can add it herself. Lines 1, 5 and 6 break that bar; line 7 does not.

## Ranked by how many traces show it

| # | Failure | Traces | Which | Severity |
| --- | --- | --- | --- | --- |
| 1 | **A skill comes back `likely` with nothing she wrote behind it.** It comes from a chip, and no quote supports it or its twin. Example: the corps chip pre-checks Safety/Site Management and Hand-Built for someone who wrote about brushing, drainage and muddy spots (gen-01). Matches the hand scores on 19 of 20; the one it misses is a wrong skill the model picked (line 6). | 22 with text, plus 3 chip-only | ai1-01, -05, -08, -11, gen-01, -02, -03, -04, -08, -10, -14, -15, -16, -17, -18, -21, -24, -25, -26, -29, -32, -33; chip only: ai1-02, gen-35, gen-36 | High: overclaims, pre-checked. **Open:** may a chip alone, with no text, ever give `likely`? It is the prototype's design; the hand scores lean no ("Jobsite Safety should not be marked likely just because they served in the military"). For the product owner. |
| 2 | **The same skill appears twice, once as its Construction twin and once as its Maintenance twin.** For example, both Brushing skills come from "Mostly brushing and lopping". This happens when her text and a chip each pick a different twin, or when one chip lists both. It reads as a duplicate, and it uses up places under the 12 cap. | 17 | ai1-01, ai1-03, ai1-08, ai1-11, gen-01, -02, -03, -04, -06, -07, -08, -09, -10, -20, -21, -25, -36 | Low: display. Both twins are real skills. |
| 3 | **Quote is a whole sentence**, so the reason line stops pointing at the words that matter. For example: "You wrote 'I helped on a few patio and retaining wall jobs, mixing materials and moving rock.'" | 10 | ai1-03, ai1-08, ai1-13, gen-11, gen-13, gen-14, gen-17, gen-23, gen-24, gen-34 | Low: the quote is still verbatim. |
| 4 | **She wrote text, the model found nothing in it, and only the chip skills came back, labelled `produced_by: rules`.** The label says the rules answered, so nobody can tell the model ran and found nothing. Six of the eight are vague or off-topic text, where finding nothing is right. gen-15 ("leading small teams") is a real miss (line 7). | 8 | gen-08, -10, -12, -15, -22, -28, -29, -32 | Medium: hides model misses. |
| 5 | **A chip skill her own words contradict**, at any confidence. Examples: the forestry chip gives both chainsaw skills to an engine crew member (gen-08), a timber cruiser (gen-10) and a parks office worker (gen-25), none of whom mention a saw. The volunteer chip gives Tread Maintenance to someone who says she "never had a formal trail job" (gen-26) and to a community-garden volunteer (gen-32). Text only ever adds skills; it never removes a chip's. Unlike line 1, this needs reading what she said, so it is a judge's job. | 6 | gen-02, -08, -10, -25, -26, -32 | High: overclaims against her own words. |
| 6 | **Names a skill her words do not describe.** <ul><li>Maintenance Specifications for "helped maintain about three miles of trail" (ai1-08; the golden says Tread Maintenance).</li><li>Crew Management for "coordinated volunteers", where no crew was led (ai1-13; the hand score let this pass).</li><li>Tread Maintenance - Mechanized for lawn "small equipment" (gen-11).</li><li>Corridor Clearing/Site Preparation for "picking up trash and moving small branches", which is closer to Debris Management (gen-18).</li><li>Trail Plan Development for "basic map updates" (gen-25).</li></ul> | 5 | ai1-08, ai1-13, gen-11, gen-18, gen-25 | High when `likely`: wrong skill, pre-checked. |
| 7 | **Misses a skill her words clearly describe.** <ul><li>Jobsite Safety for "ran the morning briefing" (ai1-03; missed in every Week 3 run too).</li><li>Mechanized for "ran a mini excavator", because the one quote went to Drainage only (ai1-12).</li><li>Communications for "wrote the monthly newsletter" (ai1-13).</li><li>Crew Management for "leading small teams", which came back only at chip-level possible (gen-15).</li></ul> | 4 | ai1-03, ai1-12, ai1-13, gen-15 | Medium: she can add it herself, so the hand scores do not fail these. |
| 8 | **Confidence misreads hedges.** "A few times" (gen-18) and "two weekends… a couple muddy spots" (gen-19) come back likely, because the hedge sits outside the quoted words. "Some bench cut" comes back check where the golden says likely (ai1-01), because the hedge word list treats "some" as a hedge. | 3 | ai1-01, gen-18, gen-19 | Medium |
| 9 | **Too slow for a phone:** over 8 s for one answer (12.2 s on ai1-01). The model path median is 5.3 s. | 2 | ai1-01, gen-34 | Medium: the persona is on poor signal. |
| 10 | **Wrong decline wording.** She picked "No trail experience yet" and wrote nothing. The decline tells her to "Pick a background", which she already did. The hand scores add that a decline should not suggest retail experience can never count (gen-31, ai1-07). | 1 | gen-37 | Low |

**Outside the fifty (a run log).** The first run of these inputs fell back to the keyword rules on 9 of 45 text inputs because of intermittent gateway errors. One of those errors was a content-policy flag, possibly from "fire" and "burns". The rerun had none. The traces now record the reason when a fallback happens.

## What went right

Recorded so a scorer is not written for a failure that does not happen:
- Every quote is verbatim from her text.
- Every id is a real framework id.
- No level was raised above Entry.
- Rejected ids are never re-offered (ai1-11).
- The cap of 12 holds (3 traces hit it).
- All four "nothing here" inputs declined correctly: ai1-06, ai1-07, gen-30 and gen-31. gen-37 also declined, with the wrong wording (line 10).

## Where my own criteria wobbled

Lines 6 and 7 involve judgment calls a second reader might make differently:
- Is "clearing brush" Site Preparation or Brushing?
- Is "building rock steps" Hand-Built or Tread Hardening?
- Is "sent emails" enough for Communications?

I counted only the cases I would argue for. These are the dimensions to settle with the product owner before a judge is asked to score them.
