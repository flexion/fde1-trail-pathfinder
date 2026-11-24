"""TC7: procedural memory for AI-1. Which wiki sections answered this kind of work before.

Without it, every request works out from scratch which sections of the skills wiki matter:
the model searches, reads, searches again. With it, the sections that backed a credited skill
last time are handed to the model up front, and it searches only for what they do not cover.

What a row holds is closed vocabulary only, checked on write:
- `subject`: a skill id, the one the wiki index ranks first for one of her sentences;
- `wiki_version`: a hash of the wiki the row was learned against;
- `chunk_ids`: wiki section ids (`<skill-id>#<section>`).
Never her text and never a model-written search query: queries copy her words (in
`ways_results.jsonl`, t-ai1-13's query repeats "work-day sign-ups"), and the page promises
"nothing you enter is saved". A row cannot carry anything she typed, because nothing that is
not an id gets in.

Staleness, two ways:
- supersede-on-write: one live row per subject. A new write marks the old one superseded.
- a validity key: a row learned against another wiki version is never returned.
Only skills that passed the evidence check (`suggest.backed`) are written, so a poisoned
wiki section that once got through cannot outlive the fix that removes it.

SQLite, one file, no server. Off unless SUGGEST_MEMORY names the file (`:memory:` works too).
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
import threading
import time

log = logging.getLogger(__name__)

SKILL_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
CHUNK_ID = re.compile(r"^[a-z0-9][a-z0-9-]*#[a-z0-9][a-z0-9-]*$")
VERSION = re.compile(r"^[0-9a-f]{8,64}$")

SCHEMA = """
CREATE TABLE IF NOT EXISTS procedures (
    id INTEGER PRIMARY KEY,
    subject TEXT NOT NULL,
    wiki_version TEXT NOT NULL,
    chunk_ids TEXT NOT NULL,
    written_at REAL NOT NULL,
    superseded_at REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS one_live_per_subject ON procedures(subject) WHERE superseded_at IS NULL;
"""


class Procedures:
    """The store. Thread-safe enough for one app process: one connection, one lock."""

    def __init__(self, path: str = ":memory:"):
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.executescript(SCHEMA)
        self.lock = threading.Lock()

    def write(self, subject: str, wiki_version: str, chunk_ids: list[str]) -> None:
        """Supersede the live row for `subject`, then insert this one. Rejects anything not an id."""
        if not SKILL_ID.match(subject):
            raise ValueError(f"subject must be a skill id, got {subject!r}")
        if not VERSION.match(wiki_version):
            raise ValueError(f"wiki_version must be a hex hash, got {wiki_version!r}")
        bad = [c for c in chunk_ids if not CHUNK_ID.match(c)]
        if bad or not chunk_ids:
            raise ValueError(f"chunk_ids must be wiki section ids, got {bad or chunk_ids!r}")
        now = time.time()
        with self.lock, self.db:
            self.db.execute("UPDATE procedures SET superseded_at = ? WHERE subject = ? AND superseded_at IS NULL",
                            (now, subject))
            self.db.execute("INSERT INTO procedures (subject, wiki_version, chunk_ids, written_at) VALUES (?, ?, ?, ?)",
                            (subject, wiki_version, json.dumps(sorted(set(chunk_ids))), now))

    def recall(self, subject: str, wiki_version: str) -> list[str]:
        """The live row's chunk ids, or [] when there is none or it was learned against another wiki."""
        with self.lock:
            row = self.db.execute("SELECT chunk_ids, wiki_version FROM procedures "
                                  "WHERE subject = ? AND superseded_at IS NULL", (subject,)).fetchone()
        if row is None:
            return []
        if row[1] != wiki_version:
            log.info("procedure for %s is from wiki %s, not %s: not used", subject, row[1][:8], wiki_version[:8])
            return []
        return json.loads(row[0])

    def rows(self) -> list[dict]:
        """Every row, superseded ones included. For the tests and for audit."""
        with self.lock:
            cur = self.db.execute("SELECT subject, wiki_version, chunk_ids, written_at, superseded_at "
                                  "FROM procedures ORDER BY id")
            return [{"subject": s, "wiki_version": v, "chunk_ids": json.loads(c), "written_at": w, "superseded_at": x}
                    for s, v, c, w, x in cur.fetchall()]


def open_store(path: str | None) -> Procedures | None:
    """The store at `path`, or None (memory off) when unset or unopenable, e.g. a read-only mount."""
    if not path:
        return None
    try:
        return Procedures(path)
    except sqlite3.Error as exc:
        log.warning("procedural memory off: cannot open %s (%s)", path, exc)
        return None
