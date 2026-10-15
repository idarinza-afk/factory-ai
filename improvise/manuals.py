"""Read machine manuals into Improvise's local knowledge.

    improvise ingest manual.pdf [--name "Tray sealer TS-200"]
    improvise ingest C:/manuals/            (every PDF / TXT / MD in the folder)

Text is extracted per page (pypdf, `pip install improvise[docs]`), saved as Markdown
under ~/.improvise/knowledge/manuals/ (searched automatically with every question),
and alarm / error code lines are indexed so the AI can look up a code quickly.
Scanned manuals have no text layer - run OCR first and ingest the resulting text.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from .tools import tool

CODE_LINE = re.compile(r"^\s*((?:E|ERR|AL|ALM|A|F|W|FLT|FAULT|ERROR|ALARM)[\s\-_.#]?\d{1,4}[A-Z]?)\b[\s:.\-–)]*(.{5,200})$",
                       re.I | re.M)


def manuals_dir() -> Path:
    from .config import load
    d = load().user_knowledge_dir / "manuals"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _pdf_pages(path: Path) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise RuntimeError("PDF support needs pypdf: pip install pypdf") from e
    return [(p.extract_text() or "") for p in PdfReader(str(path)).pages]


def ingest_file(path: str | Path, name: str | None = None) -> dict:
    path = Path(path)
    name = name or path.stem
    if path.suffix.lower() == ".pdf":
        pages = _pdf_pages(path)
    elif path.suffix.lower() in (".txt", ".md"):
        pages = [path.read_text(encoding="utf-8", errors="ignore")]
    else:
        raise ValueError(f"unsupported file type: {path.suffix}")
    chars = sum(len(p.strip()) for p in pages)
    if pages and chars / max(len(pages), 1) < 40:
        return {"file": str(path), "ingested": False,
                "message": "Almost no text found - the manual is probably scanned. Run OCR first and ingest the text."}
    slug = re.sub(r"[^\w\-]+", "_", name).strip("_")
    md = [f"# Manual: {name}\n\nSource file: {path.name}\n"]
    for i, text in enumerate(pages, 1):
        if text.strip():
            md.append(f"\n## {name} - page {i}\n\n{text.strip()}\n")
    out = manuals_dir() / f"{slug}.md"
    out.write_text("\n".join(md), encoding="utf-8")

    codes = []
    for i, text in enumerate(pages, 1):
        for m in CODE_LINE.finditer(text):
            codes.append({"code": re.sub(r"[\s\-_.#]", "", m.group(1)).upper(), "text": m.group(2).strip(), "page": i})
    idx_file = manuals_dir() / "alarm_codes.json"
    idx = json.loads(idx_file.read_text(encoding="utf-8")) if idx_file.exists() else {}
    idx[name] = codes
    idx_file.write_text(json.dumps(idx, ensure_ascii=False, indent=1), encoding="utf-8")
    import improvise.knowledge as kb
    kb._kb = None  # rebuild the search index on next use
    return {"file": str(path), "ingested": True, "pages": len(pages), "saved_as": str(out), "alarm_codes_found": len(codes)}


def ingest(path: str | Path, name: str | None = None) -> list[dict]:
    p = Path(path)
    if p.is_dir():
        return [ingest_file(f) for f in sorted(p.iterdir()) if f.suffix.lower() in (".pdf", ".txt", ".md")]
    return [ingest_file(p, name)]


@tool
def lookup_alarm_code(code: str, machine: str = "") -> list:
    """Find an alarm / error code in the ingested machine manuals (meaning and page).

    Args:
        code: the code shown on the machine, e.g. E12, AL-305, F0004
        machine: part of the manual name to narrow the search (optional)
    """
    idx_file = manuals_dir() / "alarm_codes.json"
    if not idx_file.exists():
        return [{"message": "No manuals ingested yet: improvise ingest <manual.pdf>"}]
    want = re.sub(r"[\s\-_.#]", "", code).upper()
    digits = re.sub(r"\D", "", want).lstrip("0")
    hits = []
    for name, codes in json.loads(idx_file.read_text(encoding="utf-8")).items():
        if machine and machine.lower() not in name.lower():
            continue
        for c in codes:
            cd = re.sub(r"\D", "", c["code"]).lstrip("0")
            if c["code"] == want or (digits and cd == digits and c["code"][0] == want[0]):
                hits.append({"manual": name, **c})
    return hits or [{"message": f"{code} not found in the ingested manuals; search_knowledge may still find it in the text"}]
