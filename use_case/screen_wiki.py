"""TC6: screen the skills wiki through the whole guardrail ladder before it ships.

Run from the repository root, after build_wiki.py:
    uv run python use_case/screen_wiki.py                  # screen every chunk, write the manifest
    uv run python use_case/screen_wiki.py --check          # no model: has any page changed since it was screened?
    uv run python use_case/screen_wiki.py --wiki $DATA/wiki --check    # the copy a deploy is about to bake in

The wiki is American Trails' content (trailskills.org), copied with no review step, and the
model reads it on every request. So it is screened once, at build time, instead of per
request: zero request latency, and the judge (Level 3) can run here, where a second per
chunk costs nothing to a user.

Every chunk, cut where search_chunks cuts it (1000 characters), goes through the rules and then
the judge (01_Product_Engineering/challenge/rails.py, BUILD; the classifier is declined). The judge runs
on GUARDRAIL_MODEL/GUARDRAIL_API_BASE or INJECTION_MODEL/INJECTION_API_BASE, never on the
hosted gateway: the point is to read text that may be an attack.

The manifest (use_case/wiki_screen.json, in git) holds each page's sha256 and what stopped it,
if anything. `--check` exits 1 when a page is new, changed since it was screened, or was
flagged: that page must be screened again and read by a person before the wiki ships.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "01_Product_Engineering" / "challenge"
MANIFEST = ROOT / "use_case" / "wiki_screen.json"
CHUNK_CHARS = 1000   # search_chunks hands the model text[:1000] of each chunk


def page_hashes(wiki: Path) -> dict[str, str]:
    return {p.stem: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(wiki.glob("*.md")) if p.stem != "index"}


def check(wiki: Path, manifest: Path = MANIFEST) -> int:
    if not manifest.exists():
        print(f"no manifest at {manifest}: screen the wiki first")
        return 1
    screened = json.loads(manifest.read_text(encoding="utf-8"))["pages"]
    current = page_hashes(wiki)
    new = sorted(current.keys() - screened.keys())
    changed = sorted(p for p in current.keys() & screened.keys() if current[p] != screened[p]["sha256"])
    flagged = sorted(p for p in current.keys() & screened.keys() if screened[p]["flagged"])
    for label, pages in (("new since screening", new), ("changed since screening", changed), ("flagged", flagged)):
        if pages:
            print(f"{label}: {', '.join(pages)}")
    if new or changed or flagged:
        print("re-screen these pages and have a person read them before this wiki ships")
        return 1
    print(f"all {len(current)} pages match the manifest and none was flagged")
    return 0


def screen(wiki: Path, manifest: Path = MANIFEST) -> int:
    os.environ["WIKI_DIR"] = str(wiki)
    sys.path.insert(0, str(APP))
    from rails import BUILD, app_judge, build_rails, stopped_by
    from suggest import chunks

    judge = app_judge()
    if judge is None:
        print("the judge rung needs GUARDRAIL_MODEL/GUARDRAIL_API_BASE or INJECTION_MODEL/INJECTION_API_BASE")
        return 2
    rails = build_rails(rungs=BUILD, judge=judge)
    pages: dict[str, dict] = {stem: {"sha256": sha, "flagged": []} for stem, sha in page_hashes(wiki).items()}
    started = time.perf_counter()
    for chunk in chunks():
        stem = chunk["id"].split("#")[0]
        rung = stopped_by(rails, chunk["text"][:CHUNK_CHARS])   # an unreachable judge raises: nothing is written
        if rung:
            pages[stem]["flagged"].append({"chunk": chunk["id"], "rung": rung})
            print(f"  flagged {chunk['id']} by {rung}")
    seconds = time.perf_counter() - started
    flagged = sorted(p for p, v in pages.items() if v["flagged"])
    manifest.write_text(json.dumps({
        "screened": date.today().isoformat(), "rungs": list(BUILD), "judge": judge[0],
        "chunks": len(chunks()), "seconds": round(seconds, 1), "pages": pages}, indent=2) + "\n", encoding="utf-8")
    print(f"screened {len(chunks())} chunks of {len(pages)} pages in {seconds:.0f}s with {', '.join(BUILD)} "
          f"(judge {judge[0]}); flagged pages: {', '.join(flagged) or 'none'}")
    print(f"wrote {manifest}")
    return 1 if flagged else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--wiki", type=Path, default=ROOT / "use_case" / "data" / "wiki")
    ap.add_argument("--check", action="store_true", help="compare page hashes to the manifest; no model calls")
    ap.add_argument("--manifest", type=Path, default=MANIFEST, help="where the manifest lives (default use_case/wiki_screen.json)")
    args = ap.parse_args()
    load_dotenv(ROOT / ".env", override=True)
    sys.exit(check(args.wiki, args.manifest) if args.check else screen(args.wiki, args.manifest))


if __name__ == "__main__":
    main()
