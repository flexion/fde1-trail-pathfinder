"""The stored data, and the direct lookup over it.

`data/corpus.jsonl` holds every role and training record the app may cite
(built by `use_case/build_corpus.py`). On load the records go into an
in-memory SQLite database with one row per required skill and one per skill
taught, so a question is answered by an exact query: join the role to its
requirements, join a skill to the trainings that teach it at or above a level.

This is the "direct SQL" retrieval technique from `use_case/decisions.md`.
There is no ranking anywhere in this file. A record is either the one the
question names or it is not, and the scope (`trailskills`, `golden-01`, ...)
is applied before any lookup, so two scopes that both hold a "Trail Crew
Member" can never be confused for each other.

The eval script (`use_case/evals/retrieval_compare.py`) measures this lookup
against BM25, a wiki the model navigates itself, and dense embeddings over the
same records. The numbers are what justify the decision; this file is only
what shipped.
"""

from __future__ import annotations

import json
import os
import sqlite3
from functools import cache
from pathlib import Path

from schema import RequiredSkill, SelfRating, Training

CORPUS_PATH = Path(os.getenv("CORPUS_PATH", str(Path(__file__).parent / "data" / "corpus.jsonl")))
DEFAULT_SCOPE = os.getenv("CORPUS_SCOPE", "trailskills")

LEVEL_RANK = {"Entry": 0, "Full Performance": 1, "Expert": 2}

SCHEMA = """
CREATE TABLE records (
    id TEXT PRIMARY KEY, scope TEXT NOT NULL, kind TEXT NOT NULL, title TEXT NOT NULL,
    title_key TEXT NOT NULL, fixture INTEGER NOT NULL, synthetic INTEGER NOT NULL, json TEXT NOT NULL
);
CREATE INDEX records_scope ON records(scope, kind);
CREATE TABLE role_skills (
    record_id TEXT NOT NULL REFERENCES records(id), category TEXT NOT NULL, skill TEXT NOT NULL,
    level_rank INTEGER NOT NULL, required_level TEXT NOT NULL
);
CREATE INDEX role_skills_skill ON role_skills(category, skill);
CREATE TABLE training_skills (
    record_id TEXT NOT NULL REFERENCES records(id), category TEXT NOT NULL, skill TEXT NOT NULL,
    level_rank INTEGER NOT NULL, required_level TEXT NOT NULL
);
CREATE INDEX training_skills_skill ON training_skills(category, skill);
"""


def _key(text: str) -> str:
    """Case- and whitespace-insensitive match key. Punctuation is kept on purpose:
    'Tread Maintenance - Hand tools' and 'Tread Maintenance' are different names."""
    return " ".join(text.casefold().split())


def render(record: dict) -> str:
    """One record as plain text with headings. Every technique reads this same
    text, and it is what the answer model sees, so a fact not written here cannot
    be answered from. The id is the first line so a citation is one copy away."""
    data = record["data"]
    lines = [f"[{record['id']}]"]
    if record["kind"] == "role":
        lines.append(f"# Role: {data['role']}")
        if data.get("description"):
            lines.append(data["description"])
        lines.append("## Required skills")
        for req in data["required_skills"]:
            lines.append(f"- {req['category']} / {req['skill']}: {req['required_level']}")
        if data.get("role_dependent"):
            lines.append("## Role-dependent skills (optional, depending on the job)")
            for req in data["role_dependent"]:
                lines.append(f"- {req['category']} / {req['skill']}: {req['required_level']}")
    else:
        lines.append(f"# Training: {data['title']}")
        for field in ("provider", "format", "where", "when"):
            if data.get(field):
                lines.append(f"- {field}: {data[field]}")
        cost = data.get("cost_usd")
        cost_text = data.get("cost") or ("not stated" if cost is None else ("free" if cost == 0 else f"${cost:g}"))
        if cost is not None and cost_text.lower() not in ("free",) and "$" not in cost_text:
            cost_text = f"{cost_text} (${cost:g})"
        lines.append(f"- cost: {cost_text}")
        lines.append(f"- completion evidence (proves): {data['proves']}")
        lines.append(
            "- alignment approved by a framework steward: "
            + ("yes" if data.get("alignment_approved") else "no (draft alignment)")
        )
        lines.append("## Skills taught")
        for taught in data["skills_taught"]:
            lines.append(f"- {taught['category']} / {taught['skill']}: {taught['required_level']}")
    origin = record.get("source", {})
    where = origin.get("repository") or origin.get("path", "")
    if where:
        lines.append(f"## Source\n{where}" + (f" line {origin['line']}" if origin.get("line") else ""))
    return "\n".join(lines)


class Corpus:
    """The records, queryable. Build once per process (`load()` is cached)."""

    def __init__(self, records: list[dict]):
        self.records = {r["id"]: r for r in records}
        self.db = sqlite3.connect(":memory:", check_same_thread=False)
        self.db.executescript(SCHEMA)
        for r in records:
            self.db.execute(
                "INSERT INTO records VALUES (?,?,?,?,?,?,?,?)",
                (r["id"], r["scope"], r["kind"], r["title"], _key(r["title"]),
                 int(bool(r.get("fixture"))), int(bool(r.get("synthetic"))), json.dumps(r, ensure_ascii=False)),
            )
            table = "role_skills" if r["kind"] == "role" else "training_skills"
            refs = r["data"]["required_skills"] if r["kind"] == "role" else r["data"]["skills_taught"]
            self.db.executemany(
                f"INSERT INTO {table} VALUES (?,?,?,?,?)",
                [(r["id"], x["category"], x["skill"], LEVEL_RANK[x["required_level"]], x["required_level"]) for x in refs],
            )
        self.db.commit()

    # --- plain queries ---------------------------------------------------------

    def scopes(self) -> list[str]:
        return [row[0] for row in self.db.execute("SELECT DISTINCT scope FROM records ORDER BY scope")]

    def in_scope(self, scope: str | None, kind: str | None = None) -> list[dict]:
        sql, args = "SELECT id FROM records", []
        clauses = []
        if scope is not None:
            clauses.append("scope = ?"); args.append(scope)
        if kind is not None:
            clauses.append("kind = ?"); args.append(kind)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        return [self.records[row[0]] for row in self.db.execute(sql + " ORDER BY kind DESC, id", args)]

    @staticmethod
    def _scoped(scope: str | None) -> tuple[str, list]:
        """`scope=None` means every scope. The app never does that; the eval's
        unscoped run does, to measure what the scope key is worth."""
        return ("1=1", []) if scope is None else ("r.scope = ?", [scope])

    def role(self, name: str, scope: str | None) -> dict | None:
        where, args = self._scoped(scope)
        row = self.db.execute(
            f"SELECT id FROM records r WHERE {where} AND kind = 'role' AND title_key = ? ORDER BY id LIMIT 1",
            (*args, _key(name)),
        ).fetchone()
        return self.records[row[0]] if row else None

    def training(self, title: str, scope: str | None) -> dict | None:
        where, args = self._scoped(scope)
        row = self.db.execute(
            f"SELECT id FROM records r WHERE {where} AND kind = 'training' AND title_key = ? ORDER BY id LIMIT 1",
            (*args, _key(title)),
        ).fetchone()
        return self.records[row[0]] if row else None

    def trainings_teaching(self, category: str, skill: str, scope: str | None, *, at_least: str | None = None) -> list[dict]:
        """Trainings in scope that teach this exact category+skill, at or above a level."""
        where, args = self._scoped(scope)
        rows = self.db.execute(
            "SELECT DISTINCT t.record_id FROM training_skills t JOIN records r ON r.id = t.record_id "
            f"WHERE {where} AND t.category = ? AND t.skill = ? AND t.level_rank >= ? ORDER BY t.record_id",
            (*args, category, skill, LEVEL_RANK[at_least] if at_least else 0),
        )
        return [self.records[row[0]] for row in rows]

    def trainings_for_role(self, role_record: dict, scope: str | None) -> list[dict]:
        """The catalog slice that touches any of the role's required skills: what
        Week 1 had callers pass in as `trainings`."""
        where, args = self._scoped(scope)
        rows = self.db.execute(
            "SELECT DISTINCT t.record_id FROM training_skills t JOIN records r ON r.id = t.record_id "
            "JOIN role_skills s ON s.category = t.category AND s.skill = t.skill "
            f"WHERE s.record_id = ? AND {where} ORDER BY t.record_id",
            (role_record["id"], *args),
        )
        return [self.records[row[0]] for row in rows]

    # --- typed views for pathfinder.solve() -------------------------------------

    @staticmethod
    def required_skills(role_record: dict) -> list[RequiredSkill]:
        return [RequiredSkill.model_validate(x) for x in role_record["data"]["required_skills"]]

    @staticmethod
    def as_training(record: dict) -> Training:
        d = record["data"]
        return Training(title=d["title"], skills_taught=d["skills_taught"], cost_usd=d.get("cost_usd"),
                        proves=d["proves"], alignment_approved=bool(d.get("alignment_approved")))

    # --- the question lookup -----------------------------------------------------

    def lookup(self, question: str, scope: str | None, self_ratings: list[SelfRating] | None = None,
               role: str | None = None) -> tuple[list[dict], dict]:
        """The records a question names, by exact name, within one scope.

        No ranking: a role title, training title or skill name either appears in
        the question (case-insensitive) or it does not. Returns the records in a
        fixed order (roles, named trainings, trainings for named skills) and a
        trace of what matched, so the caller can show its work.

        An empty result is an answer: nothing in this scope is named, so the
        endpoint declines instead of answering from the nearest record.
        """
        q = _key(question)
        found: dict[str, dict] = {}
        trace = {"scope": scope, "roles": [], "trainings": [], "skills": [], "skill_trainings": []}

        if role:
            if rec := self.role(role, scope):
                found[rec["id"]] = rec
                trace["roles"].append(rec["title"])

        # Role titles. A title like "Trail Crew Leader / Foreman" also matches on
        # either half, because nobody types the slash. Longest title wins ties.
        for rec in sorted(self.in_scope(scope, "role"), key=lambda r: -len(r["title"])):
            names = [rec["title"]] + [part for part in rec["title"].split(" / ") if len(part.split()) >= 2]
            if any(_key(n) in q for n in names) and rec["id"] not in found:
                found[rec["id"]] = rec
                trace["roles"].append(rec["title"])

        for rec in self.in_scope(scope, "training"):
            if _key(rec["title"]) in q:
                found[rec["id"]] = rec
                trace["trainings"].append(rec["title"])

        # Skill names the question mentions -> the trainings that teach them. The
        # role's own requirements are the vocabulary; a skill is scoped to its
        # category, so the same name in two categories is looked up twice.
        role_recs = [r for r in found.values() if r["kind"] == "role"]
        vocabulary = {(x["category"], x["skill"]) for r in role_recs for x in r["data"]["required_skills"]}
        if self_ratings:
            vocabulary |= {(s.category.value, s.skill) for s in self_ratings}
        if not vocabulary:
            where, args = self._scoped(scope)
            rows = self.db.execute(
                f"SELECT DISTINCT category, skill FROM role_skills s JOIN records r ON r.id = s.record_id WHERE {where} "
                f"UNION SELECT DISTINCT category, skill FROM training_skills t JOIN records r ON r.id = t.record_id WHERE {where}",
                (*args, *args),
            )
            vocabulary = set(rows.fetchall())
        for category, skill in sorted(vocabulary, key=lambda cs: -len(cs[1])):
            if _key(skill) in q:
                trace["skills"].append(f"{category} / {skill}")
                for rec in self.trainings_teaching(category, skill, scope):
                    if rec["id"] not in found:
                        found[rec["id"]] = rec
                        trace["skill_trainings"].append(rec["title"])

        return list(found.values()), trace


@cache
def load(path: str | Path = CORPUS_PATH) -> Corpus:
    records = [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    return Corpus(records)

