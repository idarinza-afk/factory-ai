"""Experience memory - how improvise gets better over time.

Three layers (see docs/LEARNING.md):

1. cases      - every finished job (line design, machine list, PLC program...)
                stored with what actually happened on site.
2. feedback   - corrections and rules the engineer confirms ("always add 10%
                buffer on egg lines", "this ST block passed commissioning").
3. export     - verified cases + feedback exported as a JSONL dataset for
                periodic LoRA fine-tuning.

Everything is a local SQLite file under IMPROVISE_HOME. Nothing here is
ever uploaded anywhere.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created REAL NOT NULL,
    kind TEXT NOT NULL,            -- line_design | machine_list | plc | iot | roi | other
    title TEXT NOT NULL,
    problem TEXT NOT NULL,         -- the request / requirements
    solution TEXT NOT NULL,        -- what was delivered
    outcome TEXT DEFAULT '',       -- what happened on site / lessons learned
    verified INTEGER DEFAULT 0,    -- 1 = confirmed by an engineer
    tags TEXT DEFAULT ''
);
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created REAL NOT NULL,
    topic TEXT NOT NULL,
    rule TEXT NOT NULL,            -- the correction or rule in plain words
    weight REAL DEFAULT 1.0
);
CREATE VIRTUAL TABLE IF NOT EXISTS cases_fts USING fts5(
    title, problem, solution, outcome, tags, content='cases', content_rowid='id'
);
CREATE VIRTUAL TABLE IF NOT EXISTS feedback_fts USING fts5(
    topic, rule, content='feedback', content_rowid='id'
);
CREATE TRIGGER IF NOT EXISTS cases_ai AFTER INSERT ON cases BEGIN
  INSERT INTO cases_fts(rowid, title, problem, solution, outcome, tags)
  VALUES (new.id, new.title, new.problem, new.solution, new.outcome, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS cases_au AFTER UPDATE ON cases BEGIN
  INSERT INTO cases_fts(cases_fts, rowid, title, problem, solution, outcome, tags)
  VALUES ('delete', old.id, old.title, old.problem, old.solution, old.outcome, old.tags);
  INSERT INTO cases_fts(rowid, title, problem, solution, outcome, tags)
  VALUES (new.id, new.title, new.problem, new.solution, new.outcome, new.tags);
END;
CREATE TRIGGER IF NOT EXISTS feedback_ai AFTER INSERT ON feedback BEGIN
  INSERT INTO feedback_fts(rowid, topic, rule) VALUES (new.id, new.topic, new.rule);
END;
"""


def _fts_query(text: str) -> str:
    """Turn free text into a forgiving FTS5 OR-query."""
    words = [w.strip("\"'.,;:()[]{}?!") for w in text.split()]
    words = [w for w in words if len(w) > 1]
    return " OR ".join(f'"{w}"' for w in words) or '""'


class Memory:
    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # the screen (improvise ui) answers from worker threads; SQLite's default build is thread-safe
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)

    def close(self) -> None:
        self.conn.close()

    # --- write -----------------------------------------------------------
    def add_case(self, kind: str, title: str, problem: str, solution: str,
                 outcome: str = "", verified: bool = False, tags: str = "") -> int:
        cur = self.conn.execute(
            "INSERT INTO cases(created, kind, title, problem, solution, outcome, verified, tags)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (time.time(), kind, title, problem, solution, outcome, int(verified), tags),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def update_outcome(self, case_id: int, outcome: str, verified: bool = True) -> None:
        self.conn.execute(
            "UPDATE cases SET outcome=?, verified=? WHERE id=?", (outcome, int(verified), case_id)
        )
        self.conn.commit()

    def add_feedback(self, topic: str, rule: str, weight: float = 1.0) -> int:
        cur = self.conn.execute(
            "INSERT INTO feedback(created, topic, rule, weight) VALUES (?,?,?,?)",
            (time.time(), topic, rule, weight),
        )
        self.conn.commit()
        return int(cur.lastrowid)

    def delete_feedback(self, rule_id: int) -> bool:
        cur = self.conn.execute("DELETE FROM feedback WHERE id=?", (rule_id,))
        self.conn.execute("INSERT INTO feedback_fts(feedback_fts) VALUES('rebuild')")
        self.conn.commit()
        return cur.rowcount > 0

    def list_feedback(self) -> list[dict]:
        return [dict(r) for r in self.conn.execute("SELECT id, topic, rule FROM feedback ORDER BY id")]

    # --- read ------------------------------------------------------------
    def search_cases(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT c.*, bm25(cases_fts) AS score FROM cases_fts JOIN cases c ON c.id = cases_fts.rowid"
            " WHERE cases_fts MATCH ? ORDER BY c.verified DESC, score LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def search_feedback(self, query: str, limit: int = 5) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT f.*, bm25(feedback_fts) AS score FROM feedback_fts JOIN feedback f ON f.id = feedback_fts.rowid"
            " WHERE feedback_fts MATCH ? ORDER BY f.weight DESC, score LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def context_for(self, query: str) -> str:
        """Build the 'experience' block injected into the prompt."""
        parts: list[str] = []
        rules = self.search_feedback(query)
        if rules:
            parts.append("Confirmed rules from the engineer (follow these):")
            parts += [f"- [{r['topic']}] {r['rule']}" for r in rules]
        cases = self.search_cases(query, limit=3)
        if cases:
            parts.append("Similar past cases:")
            for c in cases:
                tag = "VERIFIED" if c["verified"] else "unverified"
                parts.append(
                    f"- #{c['id']} ({c['kind']}, {tag}) {c['title']}\n"
                    f"  problem: {c['problem'][:400]}\n"
                    f"  solution: {c['solution'][:600]}\n"
                    f"  outcome: {c['outcome'][:300] or '-'}"
                )
        return "\n".join(parts)

    def stats(self) -> dict[str, int]:
        q = lambda sql: self.conn.execute(sql).fetchone()[0]  # noqa: E731
        return {
            "cases": q("SELECT COUNT(*) FROM cases"),
            "verified_cases": q("SELECT COUNT(*) FROM cases WHERE verified=1"),
            "feedback_rules": q("SELECT COUNT(*) FROM feedback"),
        }

    # --- fine-tune export ------------------------------------------------
    def export_finetune(self, path: str | Path, only_verified: bool = True) -> int:
        """Write chat-format JSONL usable by common LoRA trainers."""
        sql = "SELECT * FROM cases" + (" WHERE verified=1" if only_verified else "")
        n = 0
        with open(path, "w", encoding="utf-8") as f:
            for c in self.conn.execute(sql):
                answer = c["solution"]
                if c["outcome"]:
                    answer += f"\n\nLessons from site: {c['outcome']}"
                rec = {"messages": [
                    {"role": "system", "content": "You are improvise, a production engineering assistant."},
                    {"role": "user", "content": c["problem"]},
                    {"role": "assistant", "content": answer},
                ]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
            for r in self.conn.execute("SELECT * FROM feedback"):
                rec = {"messages": [
                    {"role": "system", "content": "You are improvise, a production engineering assistant."},
                    {"role": "user", "content": f"What is the rule for: {r['topic']}?"},
                    {"role": "assistant", "content": r["rule"]},
                ]}
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                n += 1
        return n


_default: Memory | None = None


def default_memory() -> Memory:
    global _default
    if _default is None:
        from .config import load
        _default = Memory(load().db_path)
    return _default


def register_memory_tools() -> None:
    from .tools import tool

    @tool
    def recall_experience(query: str) -> str:
        """Search past cases and confirmed engineering rules similar to a question.

        Args:
            query: keywords describing the product, line or problem
        """
        return default_memory().context_for(query) or "No related experience yet."

    @tool
    def save_case(kind: str, title: str, problem: str, solution: str) -> str:
        """Save a finished piece of work as a new case in experience memory (unverified).

        Args:
            kind: line_design, machine_list, plc, iot, roi or other
            title: short name of the job
            problem: the requirement that was given
            solution: what was delivered
        """
        cid = default_memory().add_case(kind, title, problem, solution)
        return f"Saved as case #{cid} (unverified - confirm it after site results)."
