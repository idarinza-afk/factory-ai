"""One place that decides whether an action that changes something may run.

CONFIRM(name, args) -> bool is called before any such action (running code,
external MCP tools that are not read-only). Defaults to "no". The interactive
CLI replaces it with a y/N prompt; `improvise mcp serve` lets the MCP client
(e.g. Claude Desktop) do the asking, because it shows every call to the user.
"""

from __future__ import annotations

from typing import Callable

CONFIRM: Callable[[str, dict], bool] = lambda name, args: False


def confirm(name: str, args: dict) -> bool:
    return bool(CONFIRM(name, args))
