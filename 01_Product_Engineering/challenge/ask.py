"""Answer one free-text question from the stored records, with sources.

The shape (TC3 Step 4):

    records = corpus.lookup(question, scope)     # exact names, no ranking
    facts   = render(records) [+ the computed gap, if she gave ratings]
    answer  = complete(prompt(question, facts))  # the model only puts words on facts
    return Answer(answer=..., sources=[r.id for r in records])

Two declines, and they are different:

1. The lookup finds nothing in scope, or the question asks for a training and
   the scope has no training record for it. That is decided here, in code,
   before any model call. An empty query result is an answer.
2. The records are there but the fact is not a field any of them has (a date,
   a delivery mode). Only the model can see that, so it is asked to say so,
   and its reply is checked: a number the facts do not contain means it
   invented one, and the templated fallback replaces its words.

Nothing is recorded. The model never sees any record outside the lookup.
"""

from __future__ import annotations

import json
import logging
import re

from corpus import DEFAULT_SCOPE, load, render
from pathfinder import NO_SCORE_SUMMARY, solve
from schema import Answer, Request, SelfRating

log = logging.getLogger(__name__)

SYSTEM = (
    "You answer questions for a career tool used on a phone by trail crew members. "
    "Use ONLY the records you are given. Every fact you state must come from a record, and you cite "
    "the record id in square brackets, e.g. [golden-01:role], right after the fact. "
    "If the records do not contain what the question asks for, say so plainly and set declined to true; "
    "never guess a cost, date, delivery mode, level, or course. Never use percentages. "
    "A skill is scoped to its category: the same name in two categories is two skills. "
    "A training counts for a gap only if its alignment is steward-approved and it teaches that exact "
    "category and skill at or above the required level. "
    'Reply with JSON only, no code fences: {"answer": "<plain text, at most 120 words>", "declined": true|false}'
)

TRAINING_WORDS = re.compile(r"\b(training|trainings|course|courses|class|classes|workshop|certificate|certification|credential)\b", re.I)
_NUMBER = re.compile(r"\d+(?:\.\d+)?")


def facts_for(question: str, records: list[dict], role: str | None, self_ratings: list[SelfRating] | None, scope: str) -> str:
    blocks = [render(r) for r in records]
    role_record = next((r for r in records if r["kind"] == "role"), None)
    if self_ratings and role_record is not None:
        # Her gap is computed, not retrieved: the same deterministic function the
        # product runs. The model is told the result, not asked to work it out.
        request = Request(role=role_record["data"]["role"], self_ratings=self_ratings, scope=scope)
        result = solve(request, use_model=False)
        if result.needs_review:
            blocks.append(f"[computed gap]\nCould not be scored: {result.review_reason}")
        else:
            lines = [f"[computed gap for {request.role}, from her self-ratings]"]
            for g in result.gaps:
                hers = g.her_level.value if g.her_level else "not rated"
                lines.append(f"- {g.status.value}: {g.category.value} / {g.skill} (requires {g.required_level.value}, she has {hers})")
            for step in result.next_steps:
                lines.append(f"- next step: {step.training_title} for {step.for_skill.skill}: {step.reason}")
            for ref in result.no_training_for:
                lines.append(f"- no approved training in scope for {ref.category.value} / {ref.skill}")
            blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)


def model_answer(question: str, facts: str) -> tuple[str, bool]:
    """One model call over the facts. Returns (answer text, declined) or raises.
    Shared with the eval script so every single-shot technique is judged on the
    same prompt; only the records differ."""
    from llm import complete  # here so the no-model path never imports litellm

    prompt = f"QUESTION:\n{question}\n\nRECORDS:\n{facts}\n\nAnswer from the records only, citing ids."
    raw = complete(prompt, system=SYSTEM, timeout=60)
    data = json.loads(raw[raw.find("{"): raw.rfind("}") + 1])
    return str(data["answer"]).strip(), bool(data.get("declined", False))


def invented_number(text: str, facts: str) -> bool:
    """A number the facts do not contain is an invented fact (a cost, a date)."""
    allowed = set(_NUMBER.findall(facts))
    return "%" in text or any(n not in allowed for n in _NUMBER.findall(text))


def _template(question: str, records: list[dict], reason: str) -> str:
    """The non-AI state (BR-10.7): the matching records, named, and nothing else."""
    names = "; ".join(f"{r['title']} [{r['id']}]" for r in records)
    return f"The records that match your question are: {names}. {reason}"


def answer_question(
    question: str,
    scope: str = DEFAULT_SCOPE,
    *,
    role: str | None = None,
    self_ratings: list[SelfRating] | None = None,
    use_model: bool = True,
) -> Answer:
    corpus = load()
    question = question.strip()
    if not question:
        return Answer(question=question, scope=scope, answer="Ask a question.", declined=True, reason="empty question")
    if scope not in corpus.scopes():
        return Answer(question=question, scope=scope, answer=f"There is no stored data for scope '{scope}'.",
                      declined=True, reason="unknown scope")

    records, trace = corpus.lookup(question, scope, self_ratings=self_ratings, role=role)
    sources = [r["id"] for r in records]

    # Decline 1: decided by the query, not the model.
    if not records:
        return Answer(question=question, scope=scope, declined=True, trace=trace,
                      answer="I can't answer that from the stored records: nothing in this scope matches a role, training or skill named in the question.",
                      reason="no record in scope matches the question")
    if TRAINING_WORDS.search(question) and not any(r["kind"] == "training" for r in records):
        return Answer(question=question, scope=scope, sources=sources, declined=True, trace=trace,
                      answer="I can't recommend a training from the stored records: this scope has no training record for the skills named. "
                             + "Records found: " + "; ".join(f"{r['title']} [{r['id']}]" for r in records) + ".",
                      reason="question asks for a training; no training record in scope matches")

    facts = facts_for(question, records, role, self_ratings, scope)
    if not use_model:
        return Answer(question=question, scope=scope, sources=sources, trace=trace,
                      answer=_template(question, records, "Model disabled; the records are listed, not interpreted."),
                      reason="use_model=False")

    try:
        text, declined = model_answer(question, facts)
    except Exception as exc:  # timeout, provider down, bad JSON: the template answers instead
        log.warning("ask: model unavailable, using template: %s", type(exc).__name__)
        return Answer(question=question, scope=scope, sources=sources, trace=trace,
                      answer=_template(question, records, "The model was unavailable, so the records are listed, not interpreted."),
                      reason=f"model unavailable ({type(exc).__name__})")

    # Decline 2 is the model's call, but an invented number is not: every number in
    # the answer must appear in the facts (same rule pathfinder applies to reasons).
    if invented_number(text, facts):
        return Answer(question=question, scope=scope, sources=sources, trace=trace,
                      answer=_template(question, records, "The model's wording was discarded because it contained a figure the records do not."),
                      reason="model answer contained a number not in the records")
    # Sources are every record the model was handed, so a wrong answer can be traced
    # to the passage that caused it (Week 4). Which ids the model repeated is in the trace.
    trace["cited_in_answer"] = [r["id"] for r in records if r["id"] in text]
    return Answer(question=question, scope=scope, sources=sources, declined=declined, trace=trace, answer=text)
