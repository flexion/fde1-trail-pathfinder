"""Week 4 Step 1: fifty AI-1 traces to read.

    uv run python use_case/evals/make_traces.py inputs   # write trace_inputs.jsonl (13 golden + 37 generated)
    uv run python use_case/evals/make_traces.py run      # run suggest_competencies over them -> traces.jsonl, traces.md

There are no real traces yet: AI-1 has not been in front of users. So the fifty
are the 13 golden inputs plus 37 inputs a model wrote to a spread of people
(each marked `source: generated`), to be checked against real people's words
at the demo. `traces.md` is the same thing laid out for reading by hand.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_Product_Engineering" / "challenge"
EVALS = ROOT / "use_case" / "evals"
INPUTS = EVALS / "trace_inputs.jsonl"
TRACES = EVALS / "traces.jsonl"
TRACES_MD = EVALS / "traces.md"
GENERATED = 37

# Who the generated inputs come from, and how many of each. Mostly the people AI-1
# is for, plus the inputs that should be hard: vague, off-topic, hedged, chips only.
SPREAD = [
    (6, "conservation corps or youth corps members, one to three seasons, describing crew work in their own words"),
    (4, "wildland fire or forestry workers (hotshots, engine crews, sawyers, timber cruisers)"),
    (4, "landscapers, grounds or nursery workers, or hardscape installers new to trails"),
    (3, "veterans or military members with field, engineering or leadership experience"),
    (4, "trail volunteers or trail club members, some who only helped a few times"),
    (3, "construction trades (carpenters, equipment operators, laborers)"),
    (3, "people from park, planning, nonprofit or office jobs (grants, outreach, GIS, permits, volunteer coordination)"),
    (3, "vague answers that name no task or tool, e.g. 'I like hiking and worked outside'"),
    (2, "people with nothing trail-related at all (retail, food service, software)"),
    (2, "people who exaggerate ('expert at everything', '20 years building trails') with few specifics"),
]
# Chip only, no text: nothing for a model to write, so these are fixed.
CHIP_ONLY = [["military"], ["construction", "forestry"], ["none"]]
BACKGROUNDS = ["corps", "military", "landscape", "construction", "forestry", "volunteer", "none"]

PROMPT = """Write {n} short descriptions of past work that {who} might type into a trail-careers site
that asks "Describe work you've done". First person, plain and informal, 1 to 4 sentences, the way
real people write: some typos are fine, no polish, no trail jargon unless that person would use it.
Vary length, detail and confidence. Every one has text; none is empty.

For each, also say which of these background chips they would tick (zero, one or two):
{backgrounds}

Reply with JSON only: {{"items": [{{"text": "...", "backgrounds": ["..."]}}]}}"""


def load_env():
    load_dotenv(ROOT / ".env", override=True)
    sys.path.insert(0, str(APP))
    sys.path.insert(0, str(ROOT))
    import litellm

    litellm.suppress_debug_info = True


def make_inputs() -> None:
    load_env()
    from helpers import config
    from helpers.judge import parse_json
    from helpers.llm import chat

    cfg = config.from_env(ROOT)
    rows = []
    for line in (EVALS / "golden.jsonl").read_text(encoding="utf-8").splitlines():
        g = json.loads(line)
        if g["capability"] == "AI-1":
            rows.append({"id": f"t-{g['id']}", "source": "golden", "golden": g["id"], "input": g["input"]})
    n = 0
    for count, who in SPREAD:
        reply = chat(cfg, PROMPT.format(n=count, who=who, backgrounds=", ".join(BACKGROUNDS)))
        items = (parse_json(reply) or {}).get("items", [])[:count]
        for item in items:
            if not str(item.get("text", "")).strip():
                continue   # the model left it empty; chip-only rows are CHIP_ONLY
            n += 1
            backgrounds = [b for b in item.get("backgrounds", []) if b in BACKGROUNDS]
            rows.append({"id": f"t-gen-{n:02d}", "source": "generated", "persona": who,
                         "input": {"backgrounds": backgrounds, "text": str(item.get("text", "")).strip(), "rejected": []}})
    for backgrounds in CHIP_ONLY:
        n += 1
        rows.append({"id": f"t-gen-{n:02d}", "source": "generated", "persona": "background chip only, no text",
                     "input": {"backgrounds": backgrounds, "text": "", "rejected": []}})
    INPUTS.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    print(f"{len(rows)} inputs ({n} generated, {GENERATED} wanted) -> {INPUTS.relative_to(ROOT)}")


def run() -> None:
    load_env()
    import logging

    from schema import ExperienceRequest
    from suggest import suggest

    # suggest() logs why it fell back to the rules; keep that with the trace.
    warnings: list[str] = []
    handler = logging.Handler(logging.WARNING)
    handler.emit = lambda record: warnings.append(record.getMessage())
    logging.getLogger("suggest").addHandler(handler)

    rows = [json.loads(line) for line in INPUTS.read_text(encoding="utf-8").splitlines() if line.strip()]
    traces, md = [], ["# AI-1 traces", "",
                      f"{len(rows)} runs of `suggest_competencies` (`suggest.py`), one per input in "
                      "`trace_inputs.jsonl`. Read each and write one sentence per failure in `failures.md`.", ""]
    for row in rows:
        warnings.clear()
        started = time.perf_counter()
        out = suggest(ExperienceRequest.model_validate(row["input"]))
        seconds = round(time.perf_counter() - started, 1)
        traces.append({**row, "output": json.loads(out.model_dump_json()), "seconds": seconds,
                       "fallback_reason": warnings[0][:300] if warnings else None})
        print(f"{row['id']}: {out.produced_by} declined={out.declined} {len(out.suggestions)} suggestions {seconds}s")
        md += [f"## {row['id']} ({row['source']})", "",
               f"**Backgrounds:** {', '.join(row['input']['backgrounds']) or '-'}  ",
               f"**Text:** {row['input']['text'] or '(none)'}", "",
               f"**Output** ({out.produced_by}, {seconds}s)" + (f": declined. {out.reason}" if out.declined else ":"), ""]
        if warnings:
            md += [f"> Fell back to the keyword rules: {warnings[0][:300]}", ""]
        for s in out.suggestions:
            md.append(f"- {s.confidence} · {s.level} · {s.skill} ({s.category}) — {s.reason}")
        md += ["", "---", ""]
    TRACES.write_text("".join(json.dumps(t) + "\n" for t in traces), encoding="utf-8")
    TRACES_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"-> {TRACES.relative_to(ROOT)}, {TRACES_MD.relative_to(ROOT)}")


if __name__ == "__main__":
    {"inputs": make_inputs, "run": run}[sys.argv[1] if len(sys.argv) > 1 else "run"]()
