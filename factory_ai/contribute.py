"""Community contribution: share verified experience without leaking secrets.

Flow (see CONTRIBUTING.md):
  1. factory-ai contribute          -> anonymise verified cases + rules
  2. the owner reviews EVERY record and accepts or skips it
  3. accepted records go into a contribution pack (JSONL)
  4. the pack is sent as a Pull Request to the community dataset repo
  5. maintainers review, CI scans for leaks, and the next community LoRA is trained
     and released only if it beats the previous version on the benchmark.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Callable

from .memory import Memory

PATTERNS: list[tuple[str, re.Pattern]] = [
    ("[EMAIL]", re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")),
    ("[URL]", re.compile(r"https?://\S+")),
    ("[PHONE]", re.compile(r"(?<!\d)(?:\+?\d[\d\s\-]{7,}\d)(?!\d)")),
    ("[TAX_ID]", re.compile(r"\b\d{13}\b")),
    ("[PRICE]", re.compile(r"(?:฿|\$|€|USD|THB|EUR|RMB|CNY|บาท)\s?[\d,]+(?:\.\d+)?|[\d,]+(?:\.\d+)?\s?(?:฿|บาท|THB|USD|EUR|RMB|CNY)\b", re.I)),
    ("[COMPANY]", re.compile(r"\b[\w&.\-]+(?:\s[\w&.\-]+){0,3}\s(?:Co\.,?\s?Ltd\.?|Ltd\.?|Inc\.?|PCL|Corp\.?|GmbH|LLC)\b")),
    ("[COMPANY]", re.compile(r"บริษัท\s?\S+(?:\s?จำกัด(?:\s?\(มหาชน\))?)?")),
]


def anonymise(text: str, extra_terms: list[str] | None = None) -> str:
    """Remove contact details, prices, company names and any user-listed secret terms."""
    out = text
    for term in sorted(extra_terms or [], key=len, reverse=True):
        if term.strip():
            out = re.sub(re.escape(term.strip()), "[REDACTED]", out, flags=re.I)
    for label, pat in PATTERNS:
        out = pat.sub(label, out)
    return out


def scan_for_leaks(text: str) -> list[str]:
    """Used by CI on incoming packs: report anything that still looks private."""
    return [label for label, pat in PATTERNS if pat.search(text)]


def build_pack(memory: Memory, out_path: str | Path, secret_terms: list[str] | None = None,
               approve: Callable[[dict], bool] = lambda rec: True, contributor: str = "anonymous") -> dict:
    records, skipped = [], 0
    cases = memory.conn.execute("SELECT * FROM cases WHERE verified=1").fetchall()
    rules = memory.conn.execute("SELECT * FROM feedback").fetchall()
    candidates = []
    for c in cases:
        candidates.append({
            "type": "case", "kind": c["kind"],
            "title": anonymise(c["title"], secret_terms),
            "problem": anonymise(c["problem"], secret_terms),
            "solution": anonymise(c["solution"], secret_terms),
            "outcome": anonymise(c["outcome"] or "", secret_terms),
        })
    for r in rules:
        candidates.append({"type": "rule", "topic": anonymise(r["topic"], secret_terms),
                           "rule": anonymise(r["rule"], secret_terms)})
    for rec in candidates:
        if approve(rec):
            rec["id"] = hashlib.sha256(json.dumps(rec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
            records.append(rec)
        else:
            skipped += 1
    header = {"type": "header", "format": "factory-ai-contribution/1", "created": int(time.time()),
              "contributor": contributor, "license": "CC-BY-4.0", "records": len(records)}
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(header, ensure_ascii=False) + "\n")
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    return {"file": str(out_path), "accepted": len(records), "skipped": skipped}
