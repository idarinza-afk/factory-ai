"""Connector catalogue: one command to plug Improvise into other software via MCP.

    improvise connect list
    improvise connect add freecad
    improvise connect add excel --param dir=C:/Projects/quotes
    improvise connect add grafana --env GRAFANA_URL=http://localhost:3000 --env GRAFANA_SERVICE_ACCOUNT_TOKEN=...
    improvise connect remove freecad

Entries are written to ~/.improvise/mcp.json (your machine only). Every server here
was checked to exist as an open-source MCP server (see docs/CONNECTORS.md for sources and
licences). Tools from connectors that can change something always ask before running.
Secrets (tokens) are only ever stored in your local mcp.json, never in the repository.
"""

from __future__ import annotations

import json
import os
import shutil

CATALOGUE: dict[str, dict] = {
    # CAD / 3D
    "freecad": {"category": "CAD / 3D", "about": "Control FreeCAD (needs the freecad-mcp FreeCAD add-on)",
                "command": "uvx", "args": ["freecad-mcp"], "needs": "uv"},
    "blender": {"category": "CAD / 3D", "about": "Control Blender (needs the blender-mcp Blender add-on)",
                "command": "uvx", "args": ["mcp-for-blender"], "needs": "uv"},
    "build123d": {"category": "CAD / 3D", "about": "Parametric CAD models with build123d",
                  "command": "uv", "args": ["tool", "run", "--python", "3.12", "build123d-mcp@latest"], "needs": "uv"},
    # Office / data
    "excel": {"category": "Office / data", "about": "Read and write .xlsx files in one folder (no Excel needed)",
              "command": "uvx", "args": ["excel-mcp-server", "stdio", "--allow-dir", "{dir}"], "params": ["dir"], "needs": "uv"},
    "files": {"category": "Office / data", "about": "Read/write files in chosen folders",
              "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "{dir}"], "params": ["dir"], "needs": "node"},
    "git": {"category": "Office / data", "about": "Inspect and work with a local Git repository",
            "command": "uvx", "args": ["mcp-server-git", "--repository", "{repo}"], "params": ["repo"], "needs": "uv"},
    "fetch": {"category": "Office / data", "about": "Fetch web pages as text (datasheets, standards pages)",
              "command": "uvx", "args": ["mcp-server-fetch"], "needs": "uv", "read_only": True},
    "sqlite": {"category": "Office / data", "about": "Query a SQLite database (reference server, archived but working)",
               "command": "uvx", "args": ["mcp-server-sqlite", "--db-path", "{db}"], "params": ["db"], "needs": "uv"},
    "postgres": {"category": "Office / data", "about": "Query PostgreSQL in restricted (read-only) mode",
                 "command": "uvx", "args": ["postgres-mcp", "--access-mode=restricted"], "env": ["DATABASE_URI"], "needs": "uv"},
    # Plant data / dashboards
    "influxdb3": {"category": "Plant data / dashboards", "about": "InfluxDB 3 time-series (machine data)",
                  "command": "npx", "args": ["-y", "@influxdata/influxdb3-mcp-server"],
                  "env": ["INFLUX_DB_INSTANCE_URL", "INFLUX_DB_TOKEN"], "needs": "node"},
    "grafana": {"category": "Plant data / dashboards", "about": "Grafana dashboards and queries",
                "command": "uvx", "args": ["mcp-grafana"], "env": ["GRAFANA_URL", "GRAFANA_SERVICE_ACCOUNT_TOKEN"], "needs": "uv"},
    "nodered": {"category": "Plant data / dashboards", "about": "Build and edit Node-RED flows (not on production instances)",
                "command": "npx", "args": ["-y", "@gmag11/nodered-mcp-server", "--transport=stdio"],
                "env": ["NODERED_URL", "NODERED_API_KEY"], "needs": "node"},
    # Industrial protocols / controllers
    "opcua": {"category": "Industrial", "about": "Read/write OPC UA nodes (kukapay/opcua-mcp, run from a clone)",
              "command": "python", "args": ["{clone}/main.py"], "params": ["clone"], "env": ["OPCUA_SERVER_URL"]},
    "twincat": {"category": "Industrial", "about": "Read-only Beckhoff TwinCAT access over ADS (beckhoff_mcp, pip install from clone)",
                "command": "python", "args": ["-m", "beckhoff_mcp.server"], "read_only": True},
}


def _wrap(command: str, args: list[str]) -> tuple[str, list[str]]:
    """GUI clients on Windows often cannot start npx/uvx directly."""
    if os.name == "nt" and command in ("npx", "uvx", "uv"):
        return "cmd", ["/c", command, *args]
    return command, args


def config_path():
    from .config import load
    return load().home / "mcp.json"


def _load() -> dict:
    p = config_path()
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"servers": {}}


def _save(d: dict) -> None:
    config_path().write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")


def add(name: str, params: dict[str, str] | None = None, env: dict[str, str] | None = None) -> dict:
    if name not in CATALOGUE:
        raise ValueError(f"unknown connector {name}; see: improvise connect list")
    c = CATALOGUE[name]
    params, env = params or {}, env or {}
    missing = [p for p in c.get("params", []) if p not in params]
    if missing:
        raise ValueError(f"{name} needs --param " + " --param ".join(f"{m}=..." for m in missing))
    args = [a.format(**params) for a in c["args"]]
    command, args = _wrap(c["command"].format(**params), args)
    entry = {"command": command, "args": args}
    if env or c.get("env"):
        entry["env"] = {k: env.get(k, "") for k in c.get("env", [])} | env
    if c.get("read_only"):
        entry["read_only"] = True
    d = _load()
    d.setdefault("servers", {})[name] = entry
    _save(d)
    warn = []
    tool = {"uv": "uvx", "node": "npx"}.get(c.get("needs", ""))
    if tool and shutil.which(tool) is None:
        warn.append(f"'{tool}' was not found - install {'uv (https://docs.astral.sh/uv/)' if tool == 'uvx' else 'Node.js'} first")
    empty = [k for k, v in entry.get("env", {}).items() if not v]
    if empty:
        warn.append("set " + ", ".join(empty) + " with --env KEY=VALUE")
    return {"added": name, "entry": entry, "warnings": warn}


def remove(name: str) -> bool:
    d = _load()
    gone = d.get("servers", {}).pop(name, None) is not None
    _save(d)
    return gone


def installed() -> dict:
    return _load().get("servers", {})
