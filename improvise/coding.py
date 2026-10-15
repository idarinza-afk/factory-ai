"""Coding tools: a private workspace where Improvise writes and runs code.

Many engineering jobs need a small program: a capacity simulation, a data
clean-up script, a conversion from a supplier's Excel, a chart. These tools let
the model write files and run Python - but only inside
~/.improvise/workspace (it cannot touch anything else), and running code
needs a human "yes" every time (see improvise.safety).
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from .safety import confirm
from .tools import tool

MAX_OUTPUT = 6000


def workspace() -> Path:
    from .config import load
    p = load().home / "workspace"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _safe_path(rel: str) -> Path:
    root = workspace().resolve()
    p = (root / rel).resolve()
    if p != root and root not in p.parents:
        raise ValueError("path must stay inside the Improvise workspace")
    return p


@tool
def workspace_write(path: str, content: str) -> dict:
    """Create or overwrite a text file (code, data, notes) in the Improvise workspace.

    Args:
        path: relative path inside the workspace, e.g. sim/line_sim.py
        content: full file content
    """
    p = _safe_path(path)
    if p.relative_to(workspace().resolve()).parts[:1] == (".history",):
        raise ValueError("the .history folder is read-only")
    p.parent.mkdir(parents=True, exist_ok=True)
    saved = None
    if p.exists():  # keep the previous version so broken code can always be restored
        saved = _history_dir(path) / f"{time.strftime('%Y%m%d_%H%M%S')}_{p.name}"
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, saved)
    p.write_text(content, encoding="utf-8")
    return {"written": str(p), "bytes": len(content.encode("utf-8")),
            "previous_version_saved": saved.name if saved else None}


def _history_dir(path: str) -> Path:
    rel = _safe_path(path).relative_to(workspace().resolve())
    return workspace() / ".history" / rel.parent / rel.name


@tool
def workspace_history(path: str) -> list:
    """List saved earlier versions of a workspace file (newest last).

    Args:
        path: relative path of the file
    """
    d = _history_dir(path)
    return sorted(f.name for f in d.glob("*")) if d.exists() else []


@tool
def workspace_restore(path: str, version: str = "") -> dict:
    """Restore an earlier version of a workspace file (the current one is saved first).

    Args:
        path: relative path of the file
        version: version name from workspace_history; empty = the most recent earlier version
    """
    versions = workspace_history(path)
    if not versions:
        raise ValueError("no earlier versions of this file")
    v = version or versions[-1]
    if v not in versions:
        raise ValueError(f"unknown version; available: {versions}")
    content = (_history_dir(path) / v).read_text(encoding="utf-8")
    res = workspace_write(path, content)
    return {"restored": v, **res}


@tool
def workspace_read(path: str) -> str:
    """Read a text file from the Improvise workspace.

    Args:
        path: relative path inside the workspace
    """
    p = _safe_path(path)
    text = p.read_text(encoding="utf-8", errors="replace")
    return text if len(text) <= 20000 else text[:20000] + "\n...[truncated]"


@tool
def workspace_list(folder: str = "") -> list:
    """List files in the Improvise workspace.

    Args:
        folder: relative folder, empty for the whole workspace
    """
    root = workspace()
    base = _safe_path(folder) if folder else root
    return sorted(f.relative_to(root).as_posix() for f in base.rglob("*")
                  if f.is_file() and ".history" not in f.relative_to(root).parts)[:500]


@tool
def run_python(path: str, args: list[str] | None = None, timeout_s: int = 60) -> dict:
    """Run a Python script from the workspace (needs the engineer's confirmation). Returns exit code and output.

    Args:
        path: relative path of the .py file in the workspace
        args: command-line arguments
        timeout_s: time limit in seconds (max 600)
    """
    p = _safe_path(path)
    if not p.exists() or p.suffix != ".py":
        raise ValueError("run_python needs an existing .py file in the workspace - write it first")
    args = [str(a) for a in (args or [])]
    if not confirm("run_python", {"path": path, "args": args}):
        return {"ran": False, "message": "Not executed: the engineer did not confirm running this code."}
    try:
        r = subprocess.run([sys.executable, "-I", str(p), *args], cwd=workspace(), capture_output=True,
                           text=True, timeout=min(int(timeout_s), 600))
    except subprocess.TimeoutExpired:
        return {"ran": True, "exit_code": None, "error": f"timed out after {timeout_s} s"}
    out = r.stdout[-MAX_OUTPUT:]
    err = r.stderr[-MAX_OUTPUT:]
    return {"ran": True, "exit_code": r.returncode, "stdout": out, "stderr": err}
