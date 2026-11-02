"""AI-1 step 1: find candidate skills in the wiki from her text, scored on retrieval.jsonl.

    uv run --group week3 python use_case/evals/ai1_find_skill.py
    uv run --group week3 python use_case/evals/ai1_find_skill.py --techniques bm25

Corpus: use_case/data/wiki/<skill-id>.md (55 pages, git-ignored; build with
use_case/fetch_trailskills_levels.py then use_case/build_wiki.py). One page is
one document, so a hit is a skill id, which is what the labels name.

Techniques, each ranking all 55 pages for her text, no model:
    bm25   Session 5's BM25 (rank_bm25.BM25Okapi)
    dense  cosine similarity of embeddings (EMBED_MODEL, default Titan v2 through the
           gateway), cached in use_case/data/embeddings_cache.json (git-ignored)

Decline: a ranking always has a top k, so below MIN_SCORE (the top page's score)
the answer is "nothing found". Each threshold is set between the two decline
cases and the lowest answerable case, so it is fitted to eight questions.

Twins: the same skill under two categories counts as one gold skill, and finding
either passes (EXTRA_TWINS, twin_groups).

Writes use_case/evals/ai1_find_skill_results.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]
WIKI = ROOT / "use_case" / "data" / "wiki"
CASES = ROOT / "use_case" / "evals" / "retrieval.jsonl"
OUT = ROOT / "use_case" / "evals" / "ai1_find_skill_results.md"
EMBED_CACHE = ROOT / "use_case" / "data" / "embeddings_cache.json"

KS = (5, 8, 12)
TOKEN = re.compile(r"[a-z0-9]+")
# The gateway serves no OpenAI embedding model; Titan v2 takes one text per request.
DEFAULT_EMBED_MODEL = "openai/bedrock/amazon.titan-embed-text-v2:0"
# bm25: declines score 3.3 and 6.3, lowest answerable 10.8. dense: the barista case scores
# 0.11 and answerable 0.31-0.51, but "I worked on trails" scores 0.46, so no threshold
# declines it: vague trail text is close to every page.
MIN_SCORE = {"bm25": 8.0, "dense": 0.2}


def tokenize(text: str) -> list[str]:
    return TOKEN.findall(text.lower())


def load_pages() -> dict[str, str]:
    """Skill id -> page text. The 'Category: ... · id: ... · source: ...' line keeps only the
    category: it is all that tells the Construction and Maintenance twins apart."""
    pages = {}
    for path in sorted(WIKI.glob("*.md")):
        if path.stem == "index":
            continue
        lines = [ln.split(" · ")[0] if ln.startswith("Category:") else ln
                 for ln in path.read_text(encoding="utf-8").splitlines()]
        pages[path.stem] = "\n".join(lines)
    return pages


def load_cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]


# Twins: the same skill listed under Construction and Maintenance (and Planning). Finding
# either one passes; step 2 and the category on screen decide which she has. Same-title
# twins are found from the pages; these two differ in wording and are named here.
EXTRA_TWINS = [
    {"water-management-drainage-features", "water-management-drainage-features-2"},
    {"corridor-clearing-felling-tree-removal-chainsaw-crosscut",
     "corridor-clearing-bucking-felling-hazard-tree-removal-chainsaw-crosscut"},
]


def twin_groups(pages: dict[str, str]) -> dict[str, frozenset[str]]:
    """Skill id -> its twin group (a group of one when it has no twin)."""
    by_title: dict[str, set[str]] = {}
    for sid, text in pages.items():
        by_title.setdefault(text.splitlines()[0], set()).add(sid)
    groups = [g for g in by_title.values() if len(g) > 1] + EXTRA_TWINS
    out = {sid: frozenset({sid}) for sid in pages}
    for group in groups:
        for sid in group:
            out[sid] = frozenset(group)
    return out


def match(gold: list[str], named: list[str], twins: dict[str, frozenset[str]]) -> tuple[int, int, list[str], list[str]]:
    """(gold groups found, gold groups, missed gold ids, wrong named ids), twins counting as one."""
    group = lambda sid: twins.get(sid, frozenset({sid}))  # noqa: E731
    gold_groups = {group(g) for g in gold}
    named_groups = {group(n) for n in named}
    missed = sorted(g for g in gold if group(g) not in named_groups)
    wrong = sorted(n for n in dict.fromkeys(named) if group(n) not in gold_groups)
    return len(gold_groups & named_groups), len(gold_groups), missed, wrong


class Embedder:
    """Unit-length embeddings, one request per text, cached on disk by model and text."""

    def __init__(self):
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env", override=True)
        sys.path.insert(0, str(ROOT))
        from helpers import config

        cfg = config.from_env(ROOT)
        self.kwargs = cfg.embed_kwargs()
        if not os.getenv("EMBED_MODEL") or self.kwargs["model"] == "text-embedding-3-small":
            self.kwargs["model"] = DEFAULT_EMBED_MODEL
        self.model = self.kwargs["model"]
        self.cache = json.loads(EMBED_CACHE.read_text()) if EMBED_CACHE.exists() else {}

    def _one(self, text: str) -> list[float]:
        import litellm
        from helpers.llm import with_retry

        litellm.suppress_debug_info = True
        r = with_retry(lambda: litellm.embedding(input=[text], timeout=60, **self.kwargs),
                       describe=f"embedding({self.model})")
        return r.data[0]["embedding"]

    def embed(self, texts: list[str]):
        import numpy as np

        keys = [hashlib.sha256(f"{self.model}\n{t}".encode()).hexdigest() for t in texts]
        missing = [(k, t) for k, t in zip(keys, texts) if k not in self.cache]
        if missing:
            with ThreadPoolExecutor(max_workers=8) as pool:
                for (k, _), vec in zip(missing, pool.map(lambda kt: self._one(kt[1]), missing)):
                    self.cache[k] = vec
            EMBED_CACHE.write_text(json.dumps(self.cache))
        vecs = np.asarray([self.cache[k] for k in keys], dtype=np.float32)
        return vecs / np.maximum(np.linalg.norm(vecs, axis=1, keepdims=True), 1e-9)


class BM25Retriever:
    name = "bm25"

    def __init__(self, docs: dict[str, str]):
        self.ids = list(docs)
        self.index = BM25Okapi([tokenize(docs[i]) for i in self.ids])

    def rank(self, text: str) -> list[tuple[str, float]]:
        scores = self.index.get_scores(tokenize(text))
        return sorted(zip(self.ids, scores), key=lambda pair: pair[1], reverse=True)


class DenseRetriever:
    name = "dense"

    def __init__(self, docs: dict[str, str], embedder: Embedder):
        self.ids = list(docs)
        self.embedder = embedder
        self.matrix = embedder.embed([docs[i] for i in self.ids])

    def rank(self, text: str) -> list[tuple[str, float]]:
        scores = self.matrix @ self.embedder.embed([text])[0]
        return sorted(zip(self.ids, scores.tolist()), key=lambda pair: pair[1], reverse=True)


def make_retriever(name: str, docs: dict[str, str]):
    return BM25Retriever(docs) if name == "bm25" else DenseRetriever(docs, Embedder())


def retrieve(retriever, text: str, k: int) -> list[str]:
    """Top-k skill ids, best first, or [] when the best page scores below MIN_SCORE."""
    ranked = retriever.rank(text)
    if not ranked or ranked[0][1] < MIN_SCORE[retriever.name]:
        return []
    return [sid for sid, _ in ranked[:k]]


def evaluate(retriever, cases: list[dict], twins: dict[str, frozenset[str]]) -> list[dict]:
    rows = []
    for case in cases:
        start = time.perf_counter()
        ranked = retriever.rank(case["question"])
        ms = (time.perf_counter() - start) * 1000
        order = [sid for sid, _ in ranked]
        # A twin group's rank is its best member's.
        ranks = {}
        for g in case["gold"]:
            name = " / ".join(sorted(twins[g] & set(case["gold"]))) if len(twins[g]) > 1 else g
            ranks[name] = min(order.index(t) + 1 for t in twins[g])
        row = {"id": case["id"], "kind": case["kind"], "top_score": ranked[0][1], "ms": ms, "gold_ranks": ranks}
        for k in KS:
            hits = retrieve(retriever, case["question"], k)
            if case["kind"] == "decline":
                row[f"@{k}"] = "pass" if not hits else "fail"
            else:
                found, total, _, wrong = match(case["gold"], hits, twins)
                row[f"@{k}"] = f"{found}/{total}, {len(wrong)} wrong"
        rows.append(row)
    return rows


def summary(rows: list[dict], k: int) -> dict:
    answerable = [r for r in rows if r["kind"] != "decline"]
    found = [int(r[f"@{k}"].split("/")[0]) for r in answerable]
    gold = [int(r[f"@{k}"].split("/")[1].split(",")[0]) for r in answerable]
    return {
        "all_found": sum(f == g for f, g in zip(found, gold)),
        "answerable": len(answerable),
        "recall": sum(found) / max(1, sum(gold)),
        "declines": sum(r[f"@{k}"] == "pass" for r in rows if r["kind"] == "decline"),
        "decline_cases": len(rows) - len(answerable),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--techniques", default="bm25,dense")
    args = ap.parse_args()

    pages = load_pages()
    cases = load_cases()
    twins = twin_groups(pages)
    results = {}
    for name in args.techniques.split(","):
        retriever = make_retriever(name, pages)
        results[name] = evaluate(retriever, cases, twins)

    lines = [
        "# AI-1 retrieval results (step 1: find skills, no model)",
        "",
        f"{len(pages)} wiki pages, one document per page. `{CASES.name}`: {len(cases)} questions. "
        "Decline when the top page scores below the technique's threshold. "
        "Twins (the same skill under two categories) count as one gold skill: either passes.",
        "",
        "| technique | decline below | k | all gold found | gold recall | declines correct | avg ms |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, rows in results.items():
        ms = sum(r["ms"] for r in rows) / len(rows)
        for k in KS:
            s = summary(rows, k)
            lines.append(f"| {name} | {MIN_SCORE[name]} | {k} | {s['all_found']}/{s['answerable']} | "
                         f"{s['recall']:.0%} | {s['declines']}/{s['decline_cases']} | {ms:.1f} |")
    for name, rows in results.items():
        lines += [
            "",
            f"## {name}",
            "",
            "| id | kind | top score | " + " | ".join(f"recall@{k}" for k in KS) + " | gold ranks | ms |",
            "| --- | --- | --- | " + " | ".join("---" for _ in KS) + " | --- | --- |",
        ]
        for r in rows:
            ranks = ", ".join(f"{g}: {n}" for g, n in sorted(r["gold_ranks"].items(), key=lambda kv: kv[1])) or "-"
            lines.append(f"| {r['id']} | {r['kind']} | {r['top_score']:.2f} | "
                         + " | ".join(r[f"@{k}"] for k in KS) + f" | {ranks} | {r['ms']:.1f} |")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
