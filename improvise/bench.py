"""Benchmark: measure whether a model (or a new fine-tune) is really better.

Each item in benchmarks/*.jsonl is an engineering question with:
- reference : the tool + arguments that produce the correct answer. Expected
              numbers are computed from the tools at run time, so they never
              go stale when a calculation is improved.
- checks    : numbers that must appear in the answer (with tolerance).
- must_include_any / must_not_regex : wording checks (e.g. names, no invented prices).
- expect_tools : tools the agent should have called.
- forbid_tools : tools the agent must NOT call (safety probes).
- fixtures  : experience (cases / rules) seeded into a throw-away memory first,
              to test that confirmed experience changes the answer.

Each item scores 0..1 (answer checks 80%, tool use 20%). Results are saved as
JSON so models can be compared:  improvise bench --compare old.json
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any, Callable

BENCH_DIR = Path(__file__).parent / "benchmarks"
_NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")


def load_items(path: str | Path | None = None) -> list[dict]:
    files = [Path(path)] if path else sorted(BENCH_DIR.glob("*.jsonl"))
    items = []
    for f in files:
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                items.append(json.loads(line))
    return items


def _dig(obj: Any, path: str) -> Any:
    for part in path.split("."):
        obj = obj[int(part)] if isinstance(obj, list) else obj[part]
    return obj


def expected_values(item: dict) -> list[tuple[dict, float]]:
    """Run the reference tool and return (check, expected number) pairs."""
    checks = item.get("checks", [])
    if not checks:
        return []
    result = None
    if any("ref_path" in c for c in checks):
        from .tools import load_all
        reg = load_all()
        ref = item["reference"]
        result = reg[ref["tool"]].call(ref["args"])
    out = []
    for c in checks:
        val = c["value"] if "value" in c else _dig(result, c["ref_path"])
        out.append((c, float(val)))
    return out


def numbers_in(text: str) -> list[float]:
    vals = []
    for m in _NUM.findall(text):
        try:
            vals.append(float(m.replace(",", "")))
        except ValueError:
            pass
    return vals


def _number_ok(expected: float, found: list[float], rel_tol: float, percent_ok: bool) -> bool:
    targets = [expected, expected * 1000, expected / 1000] + ([expected * 100] if percent_ok else [])  # unit scale (NL vs m3, W vs kW)
    for t in targets:
        tol = abs(t) * rel_tol if rel_tol else 1e-9
        tol = max(tol, 0.5 * 10 ** -2 if rel_tol else 1e-9)
        if any(abs(v - t) <= tol for v in found):
            return True
    return False


def grade(item: dict, answer: str, tools_called: list[str]) -> dict:
    results = []
    found = numbers_in(answer)
    for check, exp in expected_values(item):
        alts = [exp] + [float(a) for a in check.get("also_ok", [])]
        ok = any(_number_ok(e, found, check.get("rel_tol", 0.01), check.get("percent_ok", False)) for e in alts)
        results.append({"check": check.get("ref_path", "value"), "expected": exp, "ok": ok})
    low = answer.lower()
    for group in item.get("must_include_any", []):
        ok = any(word.lower() in low for word in group)
        results.append({"check": "includes one of " + "/".join(group), "ok": ok})
    if item.get("must_not_regex"):
        ok = re.search(item["must_not_regex"], answer) is None
        results.append({"check": "must not match " + item["must_not_regex"], "ok": ok})
    for t in item.get("forbid_tools", []):  # e.g. writing to a PLC without an approved plan
        results.append({"check": f"must not call {t}", "ok": t not in tools_called})
    answer_score = sum(r["ok"] for r in results) / len(results) if results else 1.0

    expected_tools = item.get("expect_tools", [])
    missing = [t for t in expected_tools if t not in tools_called]
    tool_score = 1.0 - len(missing) / len(expected_tools) if expected_tools else 1.0
    return {
        "score": round(0.8 * answer_score + 0.2 * tool_score, 3),
        "answer_score": round(answer_score, 3),
        "tool_score": round(tool_score, 3),
        "checks": results,
        "missing_tools": missing,
    }


def _seed(memory, fixtures: dict) -> None:
    for c in fixtures.get("cases", []):
        cid = memory.add_case(c["kind"], c["title"], c["problem"], c["solution"])
        if c.get("outcome"):
            memory.update_outcome(cid, c["outcome"], bool(c.get("verified")))
    for topic, rule in fixtures.get("rules", []):
        memory.add_feedback(topic, rule)


def run(model: str | None = None, items: list[dict] | None = None,
        progress: Callable[[str], None] | None = None, client=None) -> dict:
    """Run every item in a fresh agent with an isolated, throw-away memory."""
    from . import memory as memory_mod
    from .agent import Agent
    from .config import load
    from .memory import Memory

    items = items if items is not None else load_items()
    cfg = load()
    if model:
        cfg.model = model
    results = []
    real_default = memory_mod._default
    try:
        for item in items:
            with tempfile.TemporaryDirectory() as tmp:
                mem = Memory(Path(tmp) / "bench.db")
                _seed(mem, item.get("fixtures", {}))
                memory_mod._default = mem
                called: list[str] = []
                agent = Agent(cfg, on_tool=lambda n, a, r: called.append(n))
                if client is not None:
                    agent.llm = client
                t0 = time.time()
                try:
                    answer = agent.ask(item["question"])
                    error = ""
                except Exception as e:
                    answer, error = "", str(e)
                memory_mod._default = real_default
                mem.close()  # Windows cannot delete an open SQLite file
                g = grade(item, answer, called)
                g.update({"id": item["id"], "category": item.get("category", ""), "seconds": round(time.time() - t0, 1),
                          "tools_called": called, "answer": answer, "error": error})
                results.append(g)
                if progress:
                    progress(f"{item['id']:16s} score {g['score']:.2f}  ({g['seconds']} s)")
    finally:
        memory_mod._default = real_default

    by_cat: dict[str, list[float]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r["score"])
    return {
        "model": cfg.model,
        "date": time.strftime("%Y-%m-%d %H:%M"),
        "items": len(results),
        "score": round(sum(r["score"] for r in results) / len(results), 3) if results else 0.0,
        "by_category": {k: round(sum(v) / len(v), 3) for k, v in sorted(by_cat.items())},
        "results": results,
    }


def compare(new: dict, old: dict) -> str:
    lines = [f"{'':16s} {old['model'][:18]:>18s} {new['model'][:18]:>18s}   change"]
    lines.append(f"{'TOTAL':16s} {old['score']:18.3f} {new['score']:18.3f}   {new['score'] - old['score']:+.3f}")
    for cat in sorted(set(new["by_category"]) | set(old["by_category"])):
        a, b = old["by_category"].get(cat, 0), new["by_category"].get(cat, 0)
        lines.append(f"{cat:16s} {a:18.3f} {b:18.3f}   {b - a:+.3f}")
    verdict = "BETTER - ok to release" if new["score"] > old["score"] else "NOT better - do not release"
    lines.append(verdict)
    return "\n".join(lines)
