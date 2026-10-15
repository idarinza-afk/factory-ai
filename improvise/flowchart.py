"""Flowcharts first: let the engineer check the logic before anything is built.

make_flowchart writes the chart as Mermaid (.mmd, renders in GitHub, VS Code, many
editors) and as a stand-alone HTML preview, and returns a numbered text version the
model shows in chat so the user can approve or correct it.
"""

from __future__ import annotations

import html
import json
import re

from .tools import tool

SHAPES = {"start": ("([", "])"), "end": ("([", "])"), "process": ("[", "]"), "decision": ("{", "}"),
          "io": ("[/", "/]"), "subprocess": ("[[", "]]")}


def _id(x: str) -> str:
    return re.sub(r"\W", "_", str(x)) or "n"


def _label(t: str) -> str:
    return str(t).replace('"', "'").replace("\n", " ")


def to_mermaid(steps: list[dict], direction: str = "TD") -> str:
    lines = [f"flowchart {direction}"]
    for s in steps:
        a, b = SHAPES.get(s.get("type", "process"), SHAPES["process"])
        lines.append(f'    {_id(s["id"])}{a}"{_label(s["text"])}"{b}')
    for s in steps:
        nexts = s.get("next", [])
        labels = s.get("labels", [])
        for i, n in enumerate(nexts):
            lab = labels[i] if i < len(labels) and labels[i] else ""
            arrow = f' -->|"{_label(lab)}"| ' if lab else " --> "
            lines.append(f"    {_id(s['id'])}{arrow}{_id(n)}")
    return "\n".join(lines) + "\n"


def validate(steps: list[dict]) -> list[str]:
    ids = {str(s["id"]) for s in steps}
    problems = []
    if not any(s.get("type") == "start" for s in steps):
        problems.append("no start step")
    if not any(s.get("type") == "end" for s in steps):
        problems.append("no end step (fine for a continuous machine cycle - say so)")
    for s in steps:
        for n in s.get("next", []):
            if str(n) not in ids:
                problems.append(f"step {s['id']} points to unknown step {n}")
        if s.get("type") == "decision" and len(s.get("next", [])) < 2:
            problems.append(f"decision {s['id']} needs at least two exits (yes/no)")
        if s.get("type") != "end" and not s.get("next"):
            problems.append(f"step {s['id']} has no next step")
    reachable, todo = set(), [str(s["id"]) for s in steps if s.get("type") == "start"]
    by_id = {str(s["id"]): s for s in steps}
    while todo:
        x = todo.pop()
        if x in reachable or x not in by_id:
            continue
        reachable.add(x)
        todo += [str(n) for n in by_id[x].get("next", [])]
    unreach = ids - reachable
    if unreach and reachable:
        problems.append("unreachable steps: " + ", ".join(sorted(unreach)))
    return problems


@tool
def make_flowchart(title: str, steps: list[dict], direction: str = "TD") -> dict:
    """Draw a flowchart (process, machine sequence or workflow) for the user to review BEFORE building anything.

    Args:
        title: chart title
        steps: list of {"id": "s1", "text": "Start conveyor", "type": "start|process|decision|io|subprocess|end", "next": ["s2"], "labels": ["yes", "no"] (for decisions)}
        direction: TD (top-down) or LR (left-right)
    """
    from .config import load
    if not steps:
        raise ValueError("steps is empty")
    mermaid = to_mermaid(steps, direction)
    out = load().output_dir
    stem = re.sub(r"[^\w\-]+", "_", title).strip("_") or "flowchart"
    mmd = out / f"{stem}_flowchart.mmd"
    mmd.write_text(mermaid, encoding="utf-8")
    page = (f"<!doctype html><html><head><meta charset='utf-8'><title>{html.escape(title)}</title>"
            "<script src='https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js'></script></head>"
            f"<body style='font-family:Arial'><h2>{html.escape(title)}</h2><pre class='mermaid'>{html.escape(mermaid)}</pre>"
            "<script>mermaid.initialize({startOnLoad:true});</script></body></html>")
    htm = out / f"{stem}_flowchart.html"
    htm.write_text(page, encoding="utf-8")
    text = []
    for i, s in enumerate(steps, 1):
        nxt = s.get("next", [])
        labels = s.get("labels", [])
        route = ", ".join(f"{labels[j]} -> {n}" if j < len(labels) and labels[j] else f"-> {n}" for j, n in enumerate(nxt))
        text.append(f"{s['id']}. [{s.get('type', 'process')}] {s['text']}" + (f"  ({route})" if route else ""))
    return {"mermaid_file": str(mmd), "html_preview": str(htm), "problems": validate(steps),
            "text": "\n".join(text),
            "next": "Show this flowchart to the user and ask them to approve or correct it before continuing."}
