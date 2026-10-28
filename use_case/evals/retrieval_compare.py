"""TC3 Step 3: measure retrieval techniques against the ten labelled questions.

Run from the repository root (fastembed and numpy come from the week3 group):

    uv run --group week3 python use_case/evals/retrieval_compare.py            # full run, needs a model in .env
    uv run --group week3 python use_case/evals/retrieval_compare.py --no-model # retrieval only: recall, evidence, latency
    uv run --group week3 python use_case/evals/retrieval_compare.py --unscoped # rank over every scope, no scope key

Techniques, all over the same records (`01_Product_Engineering/challenge/data/corpus.jsonl`,
one chunk per record, the boundary the record already gives):

    lookup     what shipped: exact names -> SQL join, zero ranking (corpus.py), one answer call
    bm25_rag   Session 5's Agentic RAG: a BM25 index and one `search_chunks` tool the model
               calls as often as it likes (six turns max)
    dci_wiki   Session 5's direct corpus interaction: records as named pages with headings,
               an index page, `list_pages` / `grep_wiki` / `read_page`, same loop
    dense      the third: `embedding()` over every record, cosine, top-k, one answer call
    hybrid     reciprocal rank fusion of bm25 and dense ranks (k=60), top-k, one answer call

Scoring is Session 5's: the reviewed terms appear in the answer (pass), the
expected record ids are cited in the answer (cited), the trace is kept (calls,
evidence read, latency, how the loop stopped), plus recall (every gold id was
retrieved before the model saw anything). A decline passes when the answer
refuses and invents nothing from `must_not`.

Writes use_case/evals/retrieval_results[_unscoped][_nomodel].md (the table + settings)
and the matching .jsonl (every answer and trace, for reading afterwards).
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "01_Product_Engineering" / "challenge"
sys.path.insert(0, str(APP))
sys.path.insert(0, str(ROOT))

from ask import SYSTEM, TRAINING_WORDS, facts_for, invented_number, model_answer  # noqa: E402
from corpus import load, render  # noqa: E402
from schema import SelfRating  # noqa: E402

CASES = ROOT / "use_case" / "evals" / "retrieval.jsonl"
# retrieval_results.md is the canonical run (scoped, with the model). Other modes
# get a suffix so a retrieval-only or unscoped run never overwrites it.
OUT_DIR = ROOT / "use_case" / "evals"

TOP_K = 4          # evidence the single-shot techniques hand the model; 5 of 10 questions need 2 records
MAX_TURNS = 6      # Session 5's turn budget for the two agent loops
RRF_K = 60
LOCAL_EMBEDDER = "BAAI/bge-small-en-v1.5"

DECLINE_MARKERS = ("not ", "no ", "cannot", "can't", "unavailable", "does not", "doesn't", "isn't",
                   "no data", "not stated", "not specified", "don't have", "do not have", "unable")
ID_IN_TEXT = re.compile(r"\[([A-Za-z0-9:_\-]+)\]")
TOKEN = re.compile(r"[a-z0-9$]+")


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


# --- BM25, from scratch (Okapi, k1=1.5, b=0.75) --------------------------------------


class BM25:
    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = docs
        self.avgdl = sum(len(d) for d in docs) / max(1, len(docs))
        self.tf = [Counter(d) for d in docs]
        df: Counter = Counter()
        for d in docs:
            df.update(set(d))
        n = len(docs)
        self.idf = {t: math.log(1 + (n - c + 0.5) / (c + 0.5)) for t, c in df.items()}

    def scores(self, query: list[str]) -> list[float]:
        out = []
        for tf, doc in zip(self.tf, self.docs):
            dl = len(doc)
            s = 0.0
            for t in query:
                if t not in tf:
                    continue
                f = tf[t]
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * dl / self.avgdl))
            out.append(s)
        return out


# --- embeddings: the API when configured, a local ONNX model when not --------------------


class Embedder:
    def __init__(self):
        from helpers import config
        self.cfg = config.from_env(ROOT)
        self.tokens = 0
        self.backend = "api"
        self.model_id = self.cfg.embed_model
        self._local = None
        try:
            self._api(["probe"])
        except Exception as exc:
            print(f"  embedding API unavailable ({type(exc).__name__}); using local {LOCAL_EMBEDDER}")
            self.backend, self.model_id = "local", LOCAL_EMBEDDER

    def _api(self, texts):
        import litellm
        litellm.suppress_debug_info = True
        r = litellm.embedding(input=list(texts), timeout=120, **self.cfg.embed_kwargs())
        usage = getattr(r, "usage", None)
        self.tokens += int(getattr(usage, "total_tokens", 0) or 0)
        return [row["embedding"] for row in sorted(r.data, key=lambda x: x.get("index", 0))]

    def embed(self, texts: list[str]):
        import numpy as np
        if self.backend == "api":
            vecs = np.asarray(self._api(texts), dtype=np.float32)
        else:
            if self._local is None:
                from fastembed import TextEmbedding
                self._local = TextEmbedding(LOCAL_EMBEDDER)
            vecs = np.asarray(list(self._local.embed(list(texts))), dtype=np.float32)
        return vecs / np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)


# --- the model, with tools (Session 5's ask_model) ----------------------------------------


def ask_model(messages, tools):
    import litellm
    from llm import _call_kwargs
    litellm.suppress_debug_info = True
    return litellm.completion(**_call_kwargs(messages, tools=tools, timeout=120)).choices[0].message


def run_agent(question: str, system: str, tools: list, funcs: dict, max_turns: int = MAX_TURNS) -> dict:
    """Session 5's loop, unchanged in shape: call tools until the model answers."""
    messages = [{"role": "system", "content": system}, {"role": "user", "content": question}]
    trace, chars, seen = [], 0, []
    started = time.perf_counter()
    for _ in range(max_turns):
        msg = ask_model(messages, tools)
        calls = msg.tool_calls or []
        if not calls:
            return {"answer": (msg.content or "").strip(), "trace": trace, "evidence_chars": chars,
                    "latency_s": time.perf_counter() - started, "stopped": "answer", "retrieved": seen}
        shaped = [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls]
        messages.append({"role": "assistant", "content": msg.content or "", "tool_calls": shaped})
        for call in shaped:
            name = call["function"]["name"]
            try:
                args = json.loads(call["function"]["arguments"] or "{}")
                result = str(funcs[name](**args))
            except Exception as exc:
                args, result = {}, f"(tool error: {type(exc).__name__}: {exc})"
            chars += len(result)
            for rid in ID_IN_TEXT.findall(result):
                if rid not in seen:
                    seen.append(rid)
            trace.append({"tool": name, "args": args, "chars": len(result)})
            messages.append({"role": "tool", "tool_call_id": call["id"], "content": result})
    return {"answer": "(max turns reached)", "trace": trace, "evidence_chars": chars,
            "latency_s": time.perf_counter() - started, "stopped": "max_turns", "retrieved": seen}


def schema(name, description, properties, required=()):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties, "required": list(required)}}}


AGENT_SYSTEM = (
    "Answer questions about trail roles and trainings only from tool evidence. Investigate before answering. "
    "Cite every record id you rely on in square brackets, e.g. [golden-01:role]. A skill is scoped to its "
    "category. If the evidence does not contain what is asked (a date, a delivery mode, a course), say so "
    "plainly and invent nothing. Answer in plain text, at most 120 words."
)


# --- one index per scope --------------------------------------------------------------------


class Index:
    """Everything the ranked techniques need over one set of records."""

    def __init__(self, records: list[dict], embedder: Embedder | None):
        self.records = records
        self.ids = [r["id"] for r in records]
        self.pages = {r["id"]: render(r) for r in records}
        self.bm25 = BM25([tokenize(self.pages[i]) for i in self.ids])
        self.vectors = embedder.embed([self.pages[i] for i in self.ids]) if embedder else None
        self.embedder = embedder
        self.index_page = "# Index\n" + "\n".join(f"- {r['id']}: {r['kind']} — {r['title']}" for r in records)

    def bm25_rank(self, query: str) -> list[str]:
        s = self.bm25.scores(tokenize(query))
        return [self.ids[i] for i in sorted(range(len(self.ids)), key=lambda i: -s[i])]

    def dense_rank(self, query: str) -> list[str]:
        q = self.embedder.embed([query])[0]
        s = self.vectors @ q
        return [self.ids[i] for i in sorted(range(len(self.ids)), key=lambda i: -float(s[i]))]

    def hybrid_rank(self, query: str) -> list[str]:
        fused: dict[str, float] = {}
        for ranking in (self.bm25_rank(query), self.dense_rank(query)):
            for rank, rid in enumerate(ranking):
                fused[rid] = fused.get(rid, 0.0) + 1.0 / (RRF_K + rank + 1)
        return sorted(fused, key=fused.get, reverse=True)

    # tools
    def search_chunks(self, query: str, k: int = TOP_K) -> str:
        ids = self.bm25_rank(query)[: max(1, min(int(k), 8))]
        return "\n\n---\n\n".join(self.pages[i][:1500] for i in ids)

    def list_pages(self) -> str:
        return self.index_page

    def grep_wiki(self, pattern: str) -> str:
        try:
            rx = re.compile(pattern, re.I)
        except re.error:
            rx = re.compile(re.escape(pattern), re.I)
        hits = []
        for rid, text in self.pages.items():
            for n, line in enumerate(text.splitlines(), 1):
                if rx.search(line):
                    hits.append(f"[{rid}]:{n}: {line}")
        return "\n".join(hits[:40]) or "(no matches)"

    def read_page(self, page: str) -> str:
        return self.pages.get(page, f"(unknown page: {page})")

    def rag_tools(self):
        return ([schema("search_chunks", "Search ranked record chunks (BM25). Search again with a new query when evidence is incomplete.",
                        {"query": {"type": "string"}, "k": {"type": "integer"}}, ["query"])],
                {"search_chunks": self.search_chunks})

    def dci_tools(self):
        return ([schema("list_pages", "Read the index of every record page: id, kind, title.", {}),
                 schema("grep_wiki", "Search exact text or a regular expression across all record pages, with line provenance.",
                        {"pattern": {"type": "string"}}, ["pattern"]),
                 schema("read_page", "Read one complete record page by its id.", {"page": {"type": "string", "enum": self.ids}}, ["page"])],
                {"list_pages": self.list_pages, "grep_wiki": self.grep_wiki, "read_page": self.read_page})


# --- techniques --------------------------------------------------------------------------------


def single_shot(case, scope, records: list[dict], use_model: bool, calls: int) -> dict:
    """Hand the model the records and ask once. Shared by lookup, dense and hybrid."""
    ctx = case["context"]
    ratings = [SelfRating.model_validate(r) for r in ctx.get("self_ratings", [])] or None
    started = time.perf_counter()
    facts = facts_for(case["question"], records, ctx.get("role"), ratings, scope or ctx["profile_id"])
    out = {"retrieved": [r["id"] for r in records], "evidence_chars": len(facts), "trace": [], "stopped": "answer"}
    if not records:
        out.update(answer="I can't answer that from the stored records: nothing in scope matches.", declined=True,
                   calls=calls, latency_s=time.perf_counter() - started)
        return out
    if not use_model:
        out.update(answer="", declined=None, calls=calls, latency_s=time.perf_counter() - started)
        return out
    try:
        text, declined = model_answer(case["question"], facts)
        if invented_number(text, facts):
            out["note"] = "model answer contained a number not in the records"
    except Exception as exc:
        text, declined = f"(model error: {type(exc).__name__})", None
        out["stopped"] = "error"
    out.update(answer=text, declined=declined, calls=calls + 1, latency_s=time.perf_counter() - started)
    return out


def technique_lookup(case, scope, index: Index, corpus, use_model: bool) -> dict:
    ctx = case["context"]
    ratings = [SelfRating.model_validate(r) for r in ctx.get("self_ratings", [])] or None
    started = time.perf_counter()
    records, trace = corpus.lookup(case["question"], scope, self_ratings=ratings, role=ctx.get("role"))
    # The same code-side decline the endpoint applies (ask.py, decline 1).
    if records and TRAINING_WORDS.search(case["question"]) and not any(r["kind"] == "training" for r in records):
        return {"retrieved": [r["id"] for r in records], "evidence_chars": 0, "trace": [trace], "stopped": "declined_by_query",
                "answer": "I can't recommend a training from the stored records: no training record in scope matches. "
                          "Records found: " + "; ".join(f"[{r['id']}]" for r in records),
                "declined": True, "calls": 0, "latency_s": time.perf_counter() - started}
    out = single_shot(case, scope, records, use_model, calls=0)
    out["trace"] = [trace]
    out["latency_s"] += time.perf_counter() - started - out["latency_s"]
    return out


def technique_ranked(rank, case, scope, index: Index, use_model: bool) -> dict:
    started = time.perf_counter()
    ids = rank(case["question"])[:TOP_K]
    records = [index.records[index.ids.index(i)] for i in ids]
    out = single_shot(case, scope, records, use_model, calls=1)
    out["latency_s"] += time.perf_counter() - started - out["latency_s"]
    return out


def technique_agent(tools_of, case, scope, index: Index, use_model: bool, first_search=None) -> dict:
    if not use_model:
        if first_search is None:  # the wiki loop has no model-free equivalent: the model picks the pages
            return {"answer": "", "declined": None, "retrieved": [], "evidence_chars": 0, "trace": [], "calls": 0,
                    "latency_s": 0.0, "stopped": "needs_model"}
        # What the loop's first search would return: the question itself as the query, top-k.
        started = time.perf_counter()
        text = first_search(case["question"])
        return {"answer": "", "declined": None, "retrieved": ID_IN_TEXT.findall(text), "evidence_chars": len(text),
                "trace": [{"tool": "search_chunks", "args": {"query": case["question"]}, "chars": len(text)}],
                "calls": 1, "latency_s": time.perf_counter() - started, "stopped": "first_search_only"}
    tools, funcs = tools_of()
    # The agents get the same context the single-shot techniques do: her role and
    # self-ratings, in the user message. Without them the loop cannot answer the
    # "which am I close to" questions and the comparison would be unfair.
    ctx = case["context"]
    question = case["question"]
    if ctx.get("self_ratings"):
        ratings = "; ".join(f"{r['category']} / {r['skill']}: {r['level'] or 'not rated'}" for r in ctx["self_ratings"])
        question += f"\n\nMy target role: {ctx.get('role')}. My self-ratings: {ratings}."
    result = run_agent(question, AGENT_SYSTEM, tools, funcs)
    result["calls"] = len(result["trace"])
    answer = result["answer"].lower()
    result["declined"] = any(m in answer for m in DECLINE_MARKERS)
    return result


# --- scoring -----------------------------------------------------------------------------------


def normalise(text: str) -> str:
    """Dashes and quotes vary by model; a skill name must not fail on an en dash."""
    return text.lower().replace("–", "-").replace("—", "-").replace("\u2019", "'").replace("\u2018", "'")


def has_term(term: str, text: str) -> bool:
    text = normalise(text)
    return any(normalise(alt) in text for alt in term.split("|"))


def score(case: dict, result: dict) -> dict:
    gold = set(case["gold"])
    answer = normalise(result.get("answer") or "")
    retrieved = set(result.get("retrieved") or [])
    cited_ids = set(ID_IN_TEXT.findall(result.get("answer") or ""))
    row = {
        "recall": None if result.get("stopped") == "needs_model" else ((gold <= retrieved) if gold else None),
        "calls": result.get("calls", 0),
        "evidence_chars": result.get("evidence_chars", 0),
        "latency_s": round(result.get("latency_s", 0.0), 2),
        "stopped": result.get("stopped"),
    }
    if not answer:  # retrieval-only run
        row.update({"pass": None, "cited": None})
        return row
    if case["kind"] == "decline":
        refused = any(m in answer for m in DECLINE_MARKERS) or bool(result.get("declined"))
        invented = any(has_term(t, answer) for t in case.get("must_not", []))
        row["pass"] = refused and not invented
        row["cited"] = None
    else:
        row["pass"] = all(has_term(t, answer) for t in case["expected_terms"])
        row["cited"] = gold <= cited_ids
    return row


def rate(values) -> str:
    vals = [v for v in values if v is not None]
    return "n/a" if not vals else f"{sum(vals)}/{len(vals)}"


def mean(values) -> str:
    vals = [v for v in values if v is not None]
    return "n/a" if not vals else f"{sum(vals) / len(vals):.1f}"


# --- main ---------------------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-model", action="store_true", help="retrieval only: no answer calls, no agent loops")
    ap.add_argument("--unscoped", action="store_true", help="rank over every scope; the lookup searches all scopes too")
    ap.add_argument("--techniques", default="lookup,bm25_rag,dci_wiki,dense,hybrid")
    ap.add_argument("--no-dense", action="store_true", help="skip the embedding techniques")
    args = ap.parse_args()
    use_model = not args.no_model
    wanted = [t.strip() for t in args.techniques.split(",")]
    if args.no_dense:
        wanted = [t for t in wanted if t not in ("dense", "hybrid")]

    cases = [json.loads(l) for l in CASES.read_text(encoding="utf-8").splitlines() if l.strip()]
    corpus = load()
    embedder = None
    if any(t in wanted for t in ("dense", "hybrid")):
        print("preparing embedder…")
        embedder = Embedder()

    model_label = "none (retrieval only)"
    if use_model:
        from llm import MODEL, API_BASE
        model_label = MODEL + (f" via {API_BASE}" if API_BASE else "")
    print(f"model: {model_label}   scoped: {not args.unscoped}   techniques: {', '.join(wanted)}")

    indexes: dict[str | None, Index] = {}

    def index_for(scope):
        if scope not in indexes:
            indexes[scope] = Index(corpus.in_scope(scope), embedder)
        return indexes[scope]

    rows, raw = [], []
    for case in cases:
        scope = None if args.unscoped else case["context"]["profile_id"]
        index = index_for(scope)
        for name in wanted:
            if name == "lookup":
                result = technique_lookup(case, scope, index, corpus, use_model)
            elif name == "bm25_rag":
                result = technique_agent(index.rag_tools, case, scope, index, use_model, first_search=index.search_chunks)
            elif name == "dci_wiki":
                result = technique_agent(index.dci_tools, case, scope, index, use_model)
            elif name == "dense":
                result = technique_ranked(index.dense_rank, case, scope, index, use_model)
            elif name == "hybrid":
                result = technique_ranked(index.hybrid_rank, case, scope, index, use_model)
            else:
                raise SystemExit(f"unknown technique {name}")
            s = score(case, result)
            rows.append({"id": case["id"], "kind": case["kind"], "technique": name, **s})
            raw.append({"id": case["id"], "technique": name, "scoped": not args.unscoped, "gold": case["gold"],
                        "score": s, **{k: v for k, v in result.items()}})
            flag = {True: "✓", False: "✗", None: "·"}
            print(f"  {case['id']} {name:9} pass={flag[s['pass']]} cited={flag[s['cited']]} recall={flag[s['recall']]} "
                  f"calls={s['calls']} evidence={s['evidence_chars']} {s['latency_s']}s {s['stopped']}")

    suffix = ("_unscoped" if args.unscoped else "") + ("_nomodel" if args.no_model else "")
    OUT_MD = OUT_DIR / f"retrieval_results{suffix}.md"
    OUT_JSONL = OUT_DIR / f"retrieval_results{suffix}.jsonl"
    OUT_JSONL.write_text("".join(json.dumps(r, ensure_ascii=False, default=str) + "\n" for r in raw), encoding="utf-8")

    # --- the table ---
    corpus_size = {scope: len(ix.records) for scope, ix in indexes.items()}
    lines = ["# TC3 retrieval comparison", "",
             f"Run: {time.strftime('%Y-%m-%d %H:%M')} · model: {model_label} · "
             f"{'scoped (profile_id filter before ranking)' if not args.unscoped else 'UNSCOPED (ranked over every scope)'} · "
             f"{len(cases)} questions", ""]
    lines += ["| technique | pass | cited | recall | mean calls | mean evidence chars | mean latency s | stopped |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |"]
    for name in wanted:
        rs = [r for r in rows if r["technique"] == name]
        stops = Counter(r["stopped"] for r in rs)
        lines.append(f"| {name} | {rate(r['pass'] for r in rs)} | {rate(r['cited'] for r in rs)} | {rate(r['recall'] for r in rs)} | "
                     f"{mean(r['calls'] for r in rs)} | {mean(r['evidence_chars'] for r in rs)} | {mean(r['latency_s'] for r in rs)} | "
                     f"{', '.join(f'{k} {v}' for k, v in stops.items())} |")
    lines += ["", "Per question (✓ pass · ✗ fail · · not applicable):", "",
              "| question | kind | " + " | ".join(wanted) + " |", "| --- | --- | " + " | ".join("---" for _ in wanted) + " |"]
    flag = {True: "✓", False: "✗", None: "·"}
    for case in cases:
        cells = []
        for name in wanted:
            r = next(x for x in rows if x["id"] == case["id"] and x["technique"] == name)
            cells.append(f"pass {flag[r['pass']]} cite {flag[r['cited']]} recall {flag[r['recall']]} · {r['calls']} calls · {r['evidence_chars']} ch")
        lines.append(f"| {case['id']} | {case['kind']} | " + " | ".join(cells) + " |")
    lines += ["", "## Settings", "",
              f"- Model: {model_label}; temperature as the provider defaults; answer timeout 60 s",
              f"- Turn budget for the agent loops: {MAX_TURNS}; top-k for the single-shot techniques: {TOP_K}",
              "- Chunking: none. One chunk per record, rendered by `corpus.render` (the record's own boundary)",
              f"- Corpus per scope: " + ", ".join(f"{s or 'ALL'}={n}" for s, n in corpus_size.items()) + " records",
              f"- Embedding model: {embedder.model_id if embedder else 'n/a'} ({embedder.backend if embedder else 'no dense technique run'}); RRF k={RRF_K}",
              f"- Embedding tokens: " + (f"{embedder.tokens} (measured, API)" if embedder and embedder.backend == "api"
                                          else ("n/a (local ONNX model, no token accounting)" if embedder else "n/a (nothing embedded)")),
              "- Scoring: `expected_terms` / `must_not` in retrieval.jsonl; cited = every gold id appears in square brackets in the answer; recall = every gold id was retrieved before the answer call",
              f"- Raw answers and traces: `{OUT_JSONL.name}`", ""]
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(f"\nwrote {OUT_MD.relative_to(ROOT)} and {OUT_JSONL.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
