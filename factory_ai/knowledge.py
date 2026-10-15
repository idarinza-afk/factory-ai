"""Knowledge base search (simple local RAG).

Two sources are indexed:
- factory_ai/knowledge_base/*.md  - general engineering knowledge shipped with the repo
- FACTORY_AI_HOME/knowledge/**    - your own notes, datasheets converted to .md/.txt
                                     (private, stays on your machine)

Uses SQLite FTS5 (BM25) so it needs no extra install. Can be swapped for an
embedding model later without changing callers.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .memory import _fts_query

PKG_KB = Path(__file__).parent / "knowledge_base"


def _chunks(text: str, size: int = 1200) -> list[str]:
    paras, out, buf = text.split("\n\n"), [], ""
    for p in paras:
        if len(buf) + len(p) > size and buf:
            out.append(buf.strip())
            buf = ""
        buf += p + "\n\n"
    if buf.strip():
        out.append(buf.strip())
    return out


class KnowledgeBase:
    def __init__(self, extra_dirs: list[Path] | None = None):
        self.conn = sqlite3.connect(":memory:")
        self.conn.execute("CREATE VIRTUAL TABLE kb USING fts5(source, body)")
        dirs = [PKG_KB] + list(extra_dirs or [])
        for d in dirs:
            if not d.exists():
                continue
            for f in sorted(d.rglob("*")):
                if f.suffix.lower() not in {".md", ".txt"}:
                    continue
                text = f.read_text(encoding="utf-8", errors="ignore")
                for ch in _chunks(text):
                    self.conn.execute("INSERT INTO kb VALUES (?,?)", (f.name, ch))
        self.conn.commit()

    def search(self, query: str, limit: int = 4) -> list[tuple[str, str]]:
        rows = self.conn.execute(
            "SELECT source, body FROM kb WHERE kb MATCH ? ORDER BY bm25(kb) LIMIT ?",
            (_fts_query(query), limit),
        ).fetchall()
        return [(r[0], r[1]) for r in rows]


_kb: KnowledgeBase | None = None


def default_kb() -> KnowledgeBase:
    global _kb
    if _kb is None:
        from .config import load
        from .tools import load_plugins
        extra = [Path(m.KNOWLEDGE_DIR) for m in load_plugins().values() if getattr(m, "KNOWLEDGE_DIR", None)]
        _kb = KnowledgeBase(extra + [load().user_knowledge_dir])
    return _kb


def register_kb_tool() -> None:
    from .tools import tool

    @tool
    def search_knowledge(query: str) -> str:
        """Search the engineering knowledge base (line design, OEE, hygiene, user notes).

        Args:
            query: keywords to look up
        """
        hits = default_kb().search(query)
        if not hits:
            return "Nothing found in the knowledge base."
        return "\n\n---\n\n".join(f"[{src}]\n{body}" for src, body in hits)
