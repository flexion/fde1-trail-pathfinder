"""The server.

`gradio.Server` is a FastAPI app with Gradio's API engine bolted in. You get
queueing, streaming, and MCP for free, but you bring your own frontend. That
split is the point: the API is the product, the UI is disposable.
"""

import json
import os
from functools import cache
from pathlib import Path

from fastapi.responses import HTMLResponse
from gradio import Server
from pydantic import ValidationError

from ask import answer_question
from corpus import DEFAULT_SCOPE, load as load_corpus
from llm import stream_reply
from pathfinder import NO_SCORE_SUMMARY, solve
from schema import Answer, Request, Response, SelfRating

app = Server()

FRONTEND = Path(__file__).parent / "frontend" / "index.html"
SAMPLE = Path(__file__).parent / "data" / "sample.json"


# --- The API -----------------------------------------------------------------
# The `-> str` return annotation is REQUIRED. Without it Gradio infers zero
# output components and silently returns nothing. Ask us how we know.


@app.api(name="chat")
def chat(message: str, history: list | None = None) -> str:
    """Stream a reply to one user message."""
    yield from stream_reply(message, history)


@app.api(name="compare_skills_to_role")
def compare_skills_to_role(
    role: str,
    self_ratings: list,
    required_skills: list | None = None,
    trainings: list | None = None,
    scope: str = DEFAULT_SCOPE,
) -> str:
    """Compare a trail worker's self-rated skills to one trail role and name up to three next steps.

    The role's required skills and the training catalog are looked up in the
    app's stored role library by exact role name, and the record ids used come
    back in `sources`. Every required skill comes back as has, close (exactly
    one level below) or missing (two levels below, or not rated), in that
    order. Next steps are only trainings whose steward-approved skill alignment
    matches the gap's category and skill at or above the required level; close
    gaps come first, then free, then cheaper. Skills with no matching training
    are listed, not papered over. An unknown role, an unknown skill or a
    category mismatch returns needs_review=true and nothing else. No
    percentages; nothing is recorded.

    Args:
        role: The role name from the role library, exactly as listed, e.g. "Trail Crew Leader / Foreman".
        self_ratings: Her rating per skill, each {"category", "skill", "level"}; level null means not claimed yet. Levels are "Entry", "Full Performance" or "Expert"; category and skill use exact framework names.
        required_skills: Optional. Supply the role's requirements yourself, each {"category", "skill", "required_level"}, to bypass the lookup (then supply `trainings` too; `sources` comes back empty).
        trainings: Optional. The catalog slice, each {"title", "skills_taught": [required skill], "cost_usd", "proves", "alignment_approved"}. Only read when `required_skills` is supplied.
        scope: Which stored records to look in. "trailskills" (default) is the real role library; a scenario id such as "golden-01" is a test fixture.

    Returns:
        A JSON-encoded Response: gaps, next_steps, no_training_for, summary, needs_review, review_reason, sources.
    """
    try:
        request = Request(
            role=role,
            required_skills=required_skills or [],
            self_ratings=self_ratings,
            trainings=trainings or [],
            scope=scope,
        )
    except ValidationError as exc:
        # Malformed input is a no-answer, not a crash: say why and route to manual.
        first = exc.errors()[0]
        where = ".".join(str(part) for part in first["loc"])
        return Response(
            gaps=[],
            summary=NO_SCORE_SUMMARY,
            needs_review=True,
            review_reason=f"Invalid request ({exc.error_count()} problem(s)); first: {where}: {first['msg']}",
        ).model_dump_json()
    return solve(request).model_dump_json()


@app.api(name="ask_pathfinder")
def ask_pathfinder(
    question: str,
    scope: str = DEFAULT_SCOPE,
    role: str | None = None,
    self_ratings: list | None = None,
) -> str:
    """Answer one question about trail roles, their required skills, or trainings, from the stored role library, citing the records used.

    Use this for a free-text question such as "Which skills does a Trail Crew
    Member need?", "What does Trail Care School cost and what does it prove?",
    or, with `role` and `self_ratings`, "Which requirements am I close to?".
    The question is matched to records by exact role title, training title or
    skill name within `scope`; nothing is ranked or guessed. The answer names
    every record it used in square brackets and `sources` lists their ids.

    It declines (`declined: true`) in two cases, and says which: no record in
    scope matches anything the question names, or the question asks for a
    fact no record has (a session date, a delivery mode, a course the scope
    does not hold). A decline never invents a course, cost, level or date.
    Nothing is recorded.

    Args:
        question: The question, in plain words. Name the role, training or skill as it appears in the framework.
        scope: Which stored records to look in. "trailskills" (default) is the real role library; a scenario id such as "golden-01" is a test fixture.
        role: Optional. Her target role, exactly as listed, when the question is about her own gap.
        self_ratings: Optional. Her rating per skill, each {"category", "skill", "level"}; with `role`, the gap is computed and included as a fact.

    Returns:
        A JSON-encoded Answer: question, scope, answer, sources, declined, reason, trace.
    """
    try:
        ratings = [SelfRating.model_validate(r) for r in (self_ratings or [])] or None
    except ValidationError as exc:
        first = exc.errors()[0]
        return Answer(question=question, scope=scope, declined=True,
                      answer="I can't answer that: the self-ratings are malformed.",
                      reason=f"invalid self_ratings: {'.'.join(str(p) for p in first['loc'])}: {first['msg']}").model_dump_json()
    return answer_question(question, scope, role=role, self_ratings=ratings).model_dump_json()


# --- The frontend ------------------------------------------------------------
# Defining a route at "/" replaces Gradio's default UI with ours.


@app.get("/", response_class=HTMLResponse)
def homepage() -> str:
    return FRONTEND.read_text(encoding="utf-8")


@app.get("/sample")
@cache  # the file only changes with a new image, so read it once
def sample() -> dict:
    """Synthetic roles and trainings for the UI's Week 1 path. The API looks real roles up itself (see /roles)."""
    return json.loads(SAMPLE.read_text(encoding="utf-8"))


@app.get("/roles")
def roles(scope: str = DEFAULT_SCOPE) -> dict:
    """The role titles the stored corpus holds for a scope, so a caller can name one exactly."""
    corpus = load_corpus()
    return {
        "scope": scope,
        "roles": [r["title"] for r in corpus.in_scope(scope, "role")],
        "trainings": [r["title"] for r in corpus.in_scope(scope, "training")],
    }


@app.get("/health")
def health() -> dict:
    """Your future ops team will thank you. Load balancers need this."""
    return {"status": "ok", "model": os.getenv("LLM_MODEL", "gpt-4.1-mini")}


if __name__ == "__main__":
    # 0.0.0.0 so the container is reachable from the host. On your laptop this
    # is fine. On a firm network, "reachable from where, exactly?" is the
    # question this challenge wants you to go ask.
    #
    # Read the port rather than hardcoding it, so a machine that already has
    # something on 7860 can move this one without editing code.
    port = int(os.getenv("GRADIO_SERVER_PORT", "7860"))

    # Gradio announces the address it BOUND to, which is 0.0.0.0 -- not an
    # address a browser can open. Windows rejects it outright; macOS and Linux
    # quietly redirect it to localhost, which is why it looks fine on some
    # machines and broken on others. Print the one that always works.
    print(f"\n  Open http://localhost:{port} in your browser\n", flush=True)
    app.launch(server_name="0.0.0.0", server_port=port)
