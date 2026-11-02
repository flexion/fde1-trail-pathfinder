"""AI-1 step 1: find candidate skills in the wiki from her text, scored on retrieval.jsonl.

    uv run --group week3 python use_case/evals/ai1_find_skill.py
    uv run --group week3 python use_case/evals/ai1_find_skill.py --min-score 8

Corpus: use_case/data/wiki/<skill-id>.md (55 pages, git-ignored; build with
use_case/fetch_trailskills_levels.py then use_case/build_wiki.py). One page is
one document, so a hit is a skill id, which is what the labels name.

Techniques:
    bm25   Session 5's BM25 (rank_bm25.BM25Okapi) over whole pages, her text as the query

Decline: BM25 always returns k pages, so below --min-score (top page's score)
the answer is "nothing found".

Writes use_case/evals/ai1_find_skill_results.md.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

from rank_bm25 import BM25Okapi

ROOT = Path(__file__).resolve().parents[2]
WIKI = ROOT / "use_case" / "data" / "wiki"
CASES = ROOT / "use_case" / "evals" / "retrieval.jsonl"
OUT = ROOT / "use_case" / "evals" / "ai1_find_skill_results.md"

KS = (5, 8, 12)
TOKEN = re.compile(r"[a-z0-9]+")


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


class BM25Retriever:
    def __init__(self, pages: dict[str, str]):
        self.ids = list(pages)
        self.index = BM25Okapi([tokenize(pages[i]) for i in self.ids])

    def rank(self, text: str) -> list[tuple[str, float]]:
        scores = self.index.get_scores(tokenize(text))
        return sorted(zip(self.ids, scores), key=lambda pair: pair[1], reverse=True)


def retrieve(retriever: BM25Retriever, text: str, k: int, min_score: float) -> list[str]:
    """Top-k skill ids, best first, or [] when the best page scores below min_score."""
    ranked = retriever.rank(text)
    if not ranked or ranked[0][1] < min_score:
        return []
    return [sid for sid, _ in ranked[:k]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-score", type=float, default=8.0,
                    help="decline when the top page scores below this; 8 sits between the declines (3.3, 6.3) and the lowest answerable (10.8)")
    args = ap.parse_args()

    retriever = BM25Retriever(load_pages())
    cases = [json.loads(line) for line in CASES.read_text(encoding="utf-8").splitlines() if line.strip()]

    rows = []
    for case in cases:
        start = time.perf_counter()
        ranked = retriever.rank(case["question"])
        ms = (time.perf_counter() - start) * 1000
        gold = set(case["gold"])
        row = {"id": case["id"], "kind": case["kind"], "top_score": ranked[0][1], "ms": ms,
               "gold_ranks": {g: [sid for sid, _ in ranked].index(g) + 1 for g in gold}}
        for k in KS:
            hits = retrieve(retriever, case["question"], k, args.min_score)
            if case["kind"] == "decline":
                row[f"@{k}"] = "pass" if not hits else "fail"
            else:
                found = len(gold & set(hits))
                row[f"@{k}"] = f"{found}/{len(gold)}, {len(hits) - found} wrong"
        rows.append(row)

    answerable = [r for r in rows if r["kind"] != "decline"]
    lines = [
        "# AI-1 retrieval results (step 1: find skills)",
        "",
        f"Technique: BM25 (rank_bm25 BM25Okapi) over {len(retriever.ids)} wiki pages, whole page per document. "
        f"Decline when the top score < {args.min_score}.",
        "",
        "| id | kind | top score | " + " | ".join(f"recall@{k}" for k in KS) + " | gold ranks | ms |",
        "| --- | --- | --- | " + " | ".join("---" for _ in KS) + " | --- | --- |",
    ]
    for r in rows:
        ranks = ", ".join(f"{g}: {n}" for g, n in sorted(r["gold_ranks"].items(), key=lambda kv: kv[1])) or "-"
        lines.append(f"| {r['id']} | {r['kind']} | {r['top_score']:.1f} | "
                     + " | ".join(r[f"@{k}"] for k in KS) + f" | {ranks} | {r['ms']:.1f} |")
    lines.append("")
    for k in KS:
        all_found = sum(r[f"@{k}"].startswith(f"{len(r['gold_ranks'])}/") for r in answerable)
        declines = sum(r[f"@{k}"] == "pass" for r in rows if r["kind"] == "decline")
        lines.append(f"- k={k}: all gold found in {all_found}/{len(answerable)} answerable; "
                     f"declines correct {declines}/{len(rows) - len(answerable)}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
