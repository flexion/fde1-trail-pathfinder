# Evals

## `golden.jsonl`

Six authored examples from TC1. The first five establish the initial cases;
the sixth records an unresolved product question about recommendation ranking.

Each line is one object:

```json
{"input": "...", "output": "...", "why": "what makes this the right answer"}
```

The `why` field is the one that earns its keep. In Week 4 you calibrate an
LLM judge against these, and "why" is what you calibrate it on.

### Why you write these by hand

They are the fixed point of the whole cohort. A model-generated example encodes
what the model already does; a hand-written one encodes what *you* would accept,
which is the only thing worth measuring against.

| Week | What uses this file |
| --- | --- |
| 2 | Seeds for synthetic data generation — your variation axes come from these. |
| 4 | The eval harness scores against them, and the judge is calibrated on them. |
| 6 | Injection regressions get added alongside them. |
| 8 | **The bar.** A fine-tuned open model has to pass the same harness the closed one did. |

Get them wrong now and every number for the next nine weeks is measuring the
wrong thing.

### Writing good ones

- Use **real inputs** from your work, with names and identifiers removed.
- Write the output you would **actually accept**, not an idealized one.
- Include at least one **edge case** and one where the right answer is *"I don't
  know"* or *"escalate this"*. A system that never declines is not calibrated.
- Keep them short enough to read in full during review.

## `retrieval.jsonl`

The current set contains **ten questions adapted from the existing golden
fixtures**. A [readable question list](retrieval-questions.md) is also available.
These are assistant-authored
test questions, not collected user utterances or stakeholder-approved questions.
They do not by themselves satisfy the assignment's real-question provenance
requirement, and no new user-demo questions have been collected.

This set uses `retrieval-corpus.jsonl`, derived from golden inputs, **not** the
35-row TC2 `synthetic_v1.jsonl`. It is a small fixture-based development suite,
not an independent holdout or evidence that the TC2 data problem is repaired.
The first three original goldens were also shown to the TC2 generator.

One object per line retains the assignment's core fields:

```json
{"question": "...", "gold": ["<record id>", "<record id>"], "kind": "lookup | multi-hop | decline"}
```

Each case additionally has an `id`, explicit scenario `context`, an
`expected_answer` for review/scoring, and provenance naming the original golden
line and file checksum. Only the question and context are inference inputs;
never pass `gold`, `expected_answer`, or the original golden `output`/`why`
to the answering model or retrieval index.

| Question | Golden | Coverage | Kind |
| --- | --- | --- | --- |
| retrieval-01 | 1 | Required skills, categories, and levels | lookup |
| retrieval-02 | 1 | Has / close / missing from supplied self-ratings | lookup |
| retrieval-03 | 1 | Tread-maintenance gap, matching training, price, and evidence | multi-hop |
| retrieval-04 | 1 | Free drainage training meeting the role requirement | multi-hop |
| retrieval-05 | 1 | Compare two courses' prices and completion evidence | multi-hop |
| retrieval-06 | 2 | Same skill name in different categories | lookup |
| retrieval-07 | 2 | Jobsite Safety gap and the approved training match | multi-hop |
| retrieval-08 | 3 | Decline to invent a course for an empty catalog | decline |
| retrieval-09 | 5 | Do not sell unnecessary training to someone meeting the role | multi-hop |
| retrieval-10 | 1 | Decline to invent online availability or a session date | decline |

**Five of ten questions require two source records.** For this fixture record
layout, returning only one record cannot supply all evidence for those cases.
This is an evidence-count requirement, not a measured choice of retrieval
strategy. The other cases are three single-record lookups and two declines.
Some lookups also require deterministic computation against request context;
`lookup` here means one evidence record, not that the answer is a copied string.

Golden 4 remains an existing unknown-skill regression case; it is not used to
manufacture a valid role record. Golden 6 remains excluded from this suite
because its recommendation-order decision is explicitly unresolved.

### Corpus and source IDs

`retrieval-corpus.jsonl` contains **eight fixture records**, copied only from
the inputs of goldens 1, 2, 3, and 5: four scenario-specific role records and
four training records. It contains no generated answers, `why` explanations,
or self-ratings. Each record points to its original JSON field(s).

- `golden-01:role` means the role and required skills in original line 1.
- `golden-01:training-02` means the second training in original line 1.
- `profile_id` identifies the scenario; role names and training titles must
  never be used to merge different scenarios.

These IDs are pinned to the source checksum stored in the files. If the
goldens are edited or reordered, review and update both files together before
running evaluations; line-based IDs are not stable across such changes.

Apply `context.profile_id` as a scope filter before retrieval. The evaluation
assumes the existing category-scoped skill rules: compute gaps deterministically,
accept only approved alignments at the required level or higher, and do not
recommend a course to close a gap that does not exist. Approval and prices in
these fixtures are simulated, not claims about real offerings.

`gold` names every required evidence record for answerable questions. For both
decline cases it is deliberately empty: there is no record supporting a course
recommendation (08) or an availability/date claim (10). A decline can explain
the absence of information, but must not manufacture the requested facts.
The profile 3 catalog is known to be empty from the complete scoped fixture;
one search returning no results is not generally proof that a catalog is empty.
Citation recall is not applicable to empty-gold cases; review refusal behavior
separately rather than dividing by zero or counting a refusal as retrieval success.

### Scoring labels (TC3 Step 3)

Each line also carries Session 5's scoring fields. `expected_terms` lists what
a passing answer must contain (case-insensitive substrings; `a|b` means either).
The two decline cases carry `must_not` instead: a refusal that contains any of
those invented something. `retrieval_compare.py` reads both.

### The comparison

```sh
uv run --group week3 python use_case/evals/retrieval_compare.py             # scoped, with the model: the canonical run
uv run --group week3 python use_case/evals/retrieval_compare.py --unscoped   # no scope key: what ranking has to cope with
uv run --group week3 python use_case/evals/retrieval_compare.py --no-model   # retrieval only: recall, evidence, latency
```

Five techniques over the app's stored corpus (`01_Product_Engineering/challenge/data/corpus.jsonl`,
built by `use_case/build_corpus.py`): `lookup` (what shipped: exact names, SQL
join, no ranking), `bm25_rag` and `dci_wiki` (Session 5's two tool loops),
`dense` (embeddings and cosine) and `hybrid` (RRF over BM25 and dense). Results
land in `retrieval_results[_unscoped][_nomodel].md` with the raw answers and
traces in the matching `.jsonl`. The canonical file is `retrieval_results.md`.

| Week | What uses this file |
| --- | --- |
| 3 | Scores three or more retrieval techniques against each other. The decision in `decisions.md` cites the numbers. |
| 4 | The retrieval half of the eval harness — recall and completeness, tracked per change. |
| 6 | Injection regressions arrive through retrieved content; these are the questions they must not break. |

## The Week 4 harness

Technical Challenge 4 adds the files that turn this folder into a harness
every later week runs. `python use_case/evals/run.py` is the whole interface.

| File | What it is | Written in |
| --- | --- | --- |
| `failures.md` | What goes wrong, ranked, with counts — from fifty real traces. Every scorer traces back to a line here | TC4 Step 1 |
| `human_scores.jsonl` | Twenty outputs you scored by hand: `{"input", "actual", "pass", "why"}`. The judge's agreement is measured against these | TC4 Step 1 |
| `harness.py` | Your scorers, `run_eval`, `report`, `bootstrap_ci`, the judge rubric | TC4 Steps 2–3 |
| `synthetic.jsonl` | Generated failures, each with the original, the corruption and its failure mode | TC4 Step 4 |
| `scenarios.py` | Three multi-turn scenarios — goal, `knows`, `success`, `must_not` — one a refusal | TC4 Step 5 |
| `run.py` | Points the harness at your endpoint and prints the report | TC4 Step 6 |
| `baseline.json` | **The run itself**, saved with `helpers.harness.save`. Commit it | TC4 Step 6 |

| Week | What uses these files |
| --- | --- |
| 5 | The demo leads with `baseline.json`'s headline number, and the critique goes after it. |
| 6 | Every guardrail is re-run through `run.py`; the winning attack becomes a permanent case and a new line in `failures.md`. |
| 7 | Three memory tests join `scenarios.py`. |
| 8 | **The bar.** `harness.compare(harness.load("baseline.json"), finetuned)` is the pass/fail — and it refuses if the case set changed. |
| 9 | The harness gates the deploy. |
| 10 | A sampled version runs on live traffic. |
