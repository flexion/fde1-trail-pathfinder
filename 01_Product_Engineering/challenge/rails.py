"""TC6: AI-1's guardrail ladder (guardrails/), as something the app and the evals can call.

    rules_stop(text)                           # the inline rung: "rules" or None, plain `re`, no NeMo
    rails = build_rails(rungs=BUILD)           # the build-time ladder: rules, then the judge
    rails = build_rails(only="classifier")     # one rung alone, for Step 5's per-rung rows
    stopped_by(rails, text)                    # "rules" / "classifier" / "judge", or None if it passed

Where each rung runs is decided in use_case/decisions.md (Week 6). Inline, on her text in
every request: the rules only. They are the regex list in guardrails/config.yml, applied here
with `re.search` exactly as NeMo's `regex check input` applies it (ladder.py checks the two
agree on every text), so the request path needs no event loop, no model and no network.
Build time, on every wiki chunk before a wiki ships (use_case/screen_wiki.py): rules, then judge.

The judge rung reads attack text, so its endpoint is never LLM_API_BASE: GUARDRAIL_MODEL/
GUARDRAIL_API_BASE if set, else INJECTION_MODEL/INJECTION_API_BASE. With neither, a judge
rung cannot be built and the caller has to say what it skipped.

Fail closed. A rung whose action raises is reported as "error:<rung>", and a judge that
cannot be reached raises LLMCallException out of `stopped_by`. `screen()` turns both into
a block.
"""

from __future__ import annotations

import asyncio
import os
import re
from functools import cache
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
GUARDRAILS = HERE / "guardrails"

# Rung label -> NeMo flow name, in ladder order (cheapest first). The one mapping.
RUNGS = {
    "rules": "regex check input",        # Level 1
    "classifier": "classifier check input",  # Level 2
    "judge": "self check input",         # Level 3
}
FLOW_TO_RUNG = {flow: rung for rung, flow in RUNGS.items()}

# Where each rung runs (TC6, use_case/decisions.md). Inline screens her text on every request:
# rules only, no model and no network. Build time screens every wiki chunk before a wiki ships
# (use_case/screen_wiki.py): the rules and the judge, on an approved endpoint. The classifier
# is declined everywhere: measured, it caught nothing and refused three real wiki chunks.
INLINE = ("rules",)
BUILD = ("rules", "judge")

INPUT_ONLY = {"rails": {"input": True, "dialog": False, "output": False, "retrieval": False},
              "log": {"activated_rails": True}}
# What NeMo replies when an action inside a rail raised.
INTERNAL_ERROR = "internal error"

_LITELLM_PREFIXES = ("openai/", "ollama_chat/", "ollama/", "hosted_vllm/", "lm_studio/")


def injection_judge() -> tuple[str, str, str | None] | None:
    """The INJECTION_ endpoint, what measurement runs attack text through; None when unset."""
    model, base = os.getenv("INJECTION_MODEL"), os.getenv("INJECTION_API_BASE")
    return (model, base, os.getenv("INJECTION_API_KEY")) if model and base else None


def app_judge() -> tuple[str, str, str | None] | None:
    """GUARDRAIL_ if set, else the INJECTION_ endpoint, else None. Never LLM_API_BASE."""
    if os.getenv("GUARDRAIL_MODEL") and os.getenv("GUARDRAIL_API_BASE"):
        return os.environ["GUARDRAIL_MODEL"], os.environ["GUARDRAIL_API_BASE"], os.getenv("GUARDRAIL_API_KEY")
    return injection_judge()


@cache
def rule_patterns() -> tuple[re.Pattern, ...]:
    """Level 1, the inline rung: config.yml's regex_detection input patterns, compiled."""
    raw = yaml.safe_load((GUARDRAILS / "config.yml").read_text(encoding="utf-8"))
    return tuple(re.compile(p) for p in raw["rails"]["config"]["regex_detection"]["input"]["patterns"])


def rules_stop(text: str) -> str | None:
    """"rules" when any Level 1 pattern matches `text`, else None. Microseconds; no model."""
    return "rules" if any(p.search(text) for p in rule_patterns()) else None


def _model_block(judge: tuple[str, str, str | None]) -> dict:
    model, base, key = judge
    hosted = (os.getenv("LLM_API_BASE") or "").rstrip("/")
    if hosted and base.rstrip("/").removesuffix("/v1") == hosted.removesuffix("/v1"):
        raise RuntimeError(f"the guardrail judge points at LLM_API_BASE ({hosted}); attack text "
                           "never goes to the hosted gateway. Set INJECTION_API_BASE or GUARDRAIL_API_BASE.")
    for prefix in _LITELLM_PREFIXES:
        model = model.removeprefix(prefix)
    base = base.rstrip("/")
    # api_key explicit, so the client never falls back to OPENAI_API_KEY.
    return {"type": "main", "engine": "openai", "model": model,
            "parameters": {"base_url": base if base.endswith("/v1") else f"{base}/v1", "api_key": key or "none"}}


def build_rails(only: str | None = None, judge: tuple[str, str, str | None] | None = None,
                rungs: tuple[str, ...] | None = None):
    """An LLMRails from guardrails/: every flow in config.yml (the full ladder), or only `only`'s
    flow ("rules", "classifier" or "judge"), or the named `rungs` in ladder order (INLINE, BUILD).
    `judge` is (model, api_base, api_key); default `app_judge()`."""
    from nemoguardrails import LLMRails, RailsConfig

    from guardrails.actions import classify_input

    raw = yaml.safe_load((GUARDRAILS / "config.yml").read_text(encoding="utf-8"))
    if only is not None:
        rungs = (only,)
    if rungs is not None:
        unknown = set(rungs) - set(RUNGS)
        if unknown:
            raise ValueError(f"unknown rung {sorted(unknown)}; one of {list(RUNGS)}")
        raw["rails"]["input"]["flows"] = [RUNGS[r] for r in RUNGS if r in rungs]
    judge = judge or app_judge()
    if judge is not None:
        raw["models"] = [_model_block(judge)]
    elif RUNGS["judge"] in raw["rails"]["input"]["flows"]:
        raise RuntimeError("the judge rung needs GUARDRAIL_MODEL/GUARDRAIL_API_BASE or INJECTION_MODEL/"
                           "INJECTION_API_BASE; it never runs on LLM_API_BASE")
    colang = "\n".join(p.read_text(encoding="utf-8") for p in sorted(GUARDRAILS.glob("*.co")))
    rails = LLMRails(RailsConfig.from_content(yaml_content=yaml.safe_dump(raw), colang_content=colang))
    rails.register_action(classify_input, name="classify_input")
    rails.rungs = [FLOW_TO_RUNG.get(f, f) for f in raw["rails"]["input"]["flows"]]
    return rails


def _verdict(response) -> str | None:
    stopped = next((r for r in response.log.activated_rails if r.stop), None)
    if stopped is None:
        return None
    rung = FLOW_TO_RUNG.get(stopped.name, stopped.name)
    content = response.response[0]["content"] if response.response else ""
    return f"error:{rung}" if INTERNAL_ERROR in content.lower() else rung


def _messages(text: str) -> list[dict]:
    return [{"role": "user", "content": text}]


async def stopped_by_async(rails, text: str) -> str | None:
    """The rung that stopped `text`, "error:<rung>" if a rung's action raised, or None if every
    rung passed it. A judge that cannot be reached raises (LLMCallException)."""
    return _verdict(await rails.generate_async(messages=_messages(text), options=INPUT_ONLY))


def stopped_by(rails, text: str) -> str | None:
    """Sync twin of `stopped_by_async`, for plain functions (the harness scorer, ladder.py).
    Inside a running event loop (an async handler, a notebook cell) use `await
    stopped_by_async(...)`: running NeMo's sync path on a side loop leaves its model client
    bound to a closed loop."""
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return _verdict(rails.generate(messages=_messages(text), options=INPUT_ONLY))
    raise RuntimeError("stopped_by() called inside a running event loop; use `await stopped_by_async(rails, text)`")


def screen(rails, text: str) -> str | None:
    """The request-path call: like `stopped_by`, but any failure blocks ("error:<Type>").
    Use for her text (direct) and for each retrieved wiki chunk (indirect)."""
    try:
        return stopped_by(rails, text)
    except Exception as exc:
        return f"error:{type(exc).__name__}"


async def screen_async(rails, text: str) -> str | None:
    try:
        return await stopped_by_async(rails, text)
    except Exception as exc:
        return f"error:{type(exc).__name__}"


# A wiki chunk goes through the same rungs as her text; the names say which door.
screen_chunk = screen
