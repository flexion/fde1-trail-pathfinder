# Synthetic failures (Week 4 Step 4)

**Natural vs generated.** The fifty traces showed 31 failures across these modes (counted per trace, from failures.md; five of the ten modes never happened). Generated here: **129** broken outputs from 16 correct ones (the 13 AI-1 goldens and the oracle's answer for the three generated decline cases).

Each cell: the share of that mode's broken outputs the scorer caught (scored it below 1).

| mode | exercises | natural | generated | valid_output | declines_when_it_should | decline_wording | quote_is_a_phrase | labelled_by_source | judge |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| unrelated_chip_skill (easy) | line 5: a pre-checked chip skill her words do not relate to | 6 | 7 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| unrelated_chip_skill (hard) | line 5: a pre-checked chip skill her words do not relate to |  | 7 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.57 |
| wrong_skill_for_quote (easy) | line 6: names a skill her words do not describe | 5 | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 |
| wrong_skill_for_quote (hard) | line 6: names a skill her words do not describe |  | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.67 |
| whole_sentence_quote (easy) | line 3: quote is a whole sentence of more than eight words | 9 | 9 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 |
| rules_label_with_text (easy) | line 4: she wrote text, the answer says the rules produced it | 8 | 9 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 0.00 |
| decline_asks_for_picked_background (easy) | line 10: a decline asks for a background she picked | 3 | 3 | 0.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 |
| invented_quote (easy) | guard: every quote is verbatim | 0 | 9 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| invented_quote (hard) | guard: every quote is verbatim |  | 9 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| unknown_skill_id (easy) | guard: every id is a real framework id | 0 | 11 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.18 |
| unknown_skill_id (hard) | guard: every id is a real framework id |  | 11 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.09 |
| level_raised_without_basis (easy) | guard: nothing above Entry without a cited line | 0 | 9 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| level_raised_without_basis (hard) | guard: nothing above Entry without a cited line |  | 9 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.11 |
| declines_when_she_said_enough (easy) | guard: declines only when it should | 0 | 9 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.00 |
| answers_when_it_should_decline (easy) | guard: declines when it should | 0 | 5 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.80 |
| answers_when_it_should_decline (hard) | guard: declines when it should |  | 4 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 | 0.25 |
| *unbroken originals (false alarms)* | | | 16 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.06 |

Judge calls: 145, 264,181 tokens, 560 s (measured).
