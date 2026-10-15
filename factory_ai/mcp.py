"""Model Context Protocol (MCP) support, dependency-free (JSON-RPC over stdio).

Server  - `factory-ai mcp` exposes every factory-ai tool to any MCP client
          (Claude Desktop, other agents). It also exposes teaching tools
          (add_rule, verify_case, memory_stats) so an assistant working with
          the engineer can record confirmed experience. Teaching tools are
          NOT given to the local model itself: it must not confirm its own work.

Client  - factory-ai can use other MCP servers listed in ~/.factory-ai/mcp.json
          (3D/CAD, MQTT, OPC UA, PLC IDE bridges...). Their tools appear to
          the local model as <server>__<tool>. Any tool that may change
          something (not marked read-only) needs a human "yes" for every call.

mcp.json example:
{
  "servers": {
    "blender": {"command": "uvx", "args": ["blender-mcp"]},
    "mqtt":    {"command": "python", "args": ["-m", "my_mqtt_mcp"], "env": {}, "read_only": true}
  }
}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any, Callable

from . import __version__

PROTOCOL_VERSION = "2025-06-18"

# --------------------------------------------------------------------------- server


def _teaching_tools() -> dict[str, dict]:
    from .memory import default_memory

    def add_rule(topic: str, rule: str) -> str:
        rid = default_memory().add_feedback(topic, rule)
        return f"Rule #{rid} saved."

    def verify_case(case_id: int, outcome: str) -> str:
        default_memory().update_outcome(int(case_id), outcome, True)
        return f"Case #{case_id} marked verified."

    def add_verified_case(kind: str, title: str, problem: str, solution: str, outcome: str) -> str:
        m = default_memory()
        cid = m.add_case(kind, title, problem, solution, outcome, verified=True)
        return f"Verified case #{cid} saved."

    def memory_stats() -> dict:
        return default_memory().stats()

    s = lambda **p: {"type": "object", "properties": {k: {"type": v} for k, v in p.items()}, "required": list(p)}  # noqa: E731
    return {
        "add_rule": {"fn": add_rule, "description": "Save an engineering rule the engineer has confirmed (overrides general knowledge).",
                     "schema": s(topic="string", rule="string")},
        "verify_case": {"fn": verify_case, "description": "Mark a saved case as verified with the real on-site outcome or lesson learned.",
                        "schema": s(case_id="integer", outcome="string")},
        "add_verified_case": {"fn": add_verified_case, "description": "Save a finished job that the engineer confirmed, with its on-site outcome. kind: line_design, machine_list, plc, iot, roi or other.",
                              "schema": s(kind="string", title="string", problem="string", solution="string", outcome="string")},
        "memory_stats": {"fn": memory_stats, "description": "Count of cases, verified cases and rules in experience memory.",
                         "schema": {"type": "object", "properties": {}}},
    }


class Server:
    def __init__(self):
        from .knowledge import register_kb_tool
        from .tools import REGISTRY, load_all
        load_all()
        register_kb_tool()
        self.tools = {k: v for k, v in REGISTRY.items() if "__" not in k}  # never re-export client proxies
        self.teach = _teaching_tools()

    def list_tools(self) -> list[dict]:
        out = [{"name": t.name, "description": t.description, "inputSchema": t.parameters} for t in self.tools.values()]
        out += [{"name": n, "description": d["description"], "inputSchema": d["schema"]} for n, d in self.teach.items()]
        return out

    def call(self, name: str, args: dict) -> dict:
        try:
            if name in self.tools:
                result = self.tools[name].call(args or {})
            elif name in self.teach:
                result = self.teach[name]["fn"](**(args or {}))
            else:
                return {"content": [{"type": "text", "text": f"Unknown tool {name}"}], "isError": True}
            text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str, indent=2)
            return {"content": [{"type": "text", "text": text}], "isError": False}
        except Exception as e:
            return {"content": [{"type": "text", "text": f"Error: {e}"}], "isError": True}

    def handle(self, msg: dict) -> dict | None:
        method, mid = msg.get("method"), msg.get("id")
        if mid is None:  # notification
            return None
        try:
            if method == "initialize":
                result = {
                    "protocolVersion": msg.get("params", {}).get("protocolVersion", PROTOCOL_VERSION),
                    "capabilities": {"tools": {"listChanged": False}},
                    "serverInfo": {"name": "factory-ai", "version": __version__},
                    "instructions": "Production engineering tools. Use the calculation tools for every number. "
                                    "Only use add_rule / verify_case / add_verified_case for information the engineer has confirmed.",
                }
            elif method == "tools/list":
                result = {"tools": self.list_tools()}
            elif method == "tools/call":
                p = msg.get("params", {})
                result = self.call(p.get("name", ""), p.get("arguments") or {})
            elif method == "ping":
                result = {}
            else:
                return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"Method not found: {method}"}}
            return {"jsonrpc": "2.0", "id": mid, "result": result}
        except Exception as e:
            return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32603, "message": str(e)}}


def serve(stdin=None, stdout=None) -> None:
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    # keep stdout clean for JSON-RPC: anything printed by tools goes to stderr
    real_stdout, sys.stdout = sys.stdout, sys.stderr
    try:
        server = Server()
        for line in stdin:
            line = line.strip()
            if not line:
                continue
            try:
                msg = json.loads(line)
            except json.JSONDecodeError:
                continue
            reply = server.handle(msg)
            if reply is not None:
                stdout.write(json.dumps(reply, ensure_ascii=False) + "\n")
                stdout.flush()
    finally:
        sys.stdout = real_stdout


# --------------------------------------------------------------------------- client

WRITE_WORDS = ("write", "set", "delete", "remove", "download", "upload", "start", "stop", "run", "execute",
               "create", "update", "publish", "send", "move", "save", "deploy", "force")


class MCPClient:
    def __init__(self, name: str, command: str, args: list[str] | None = None, env: dict | None = None,
                 timeout: float = 60):
        self.name = name
        self.timeout = timeout
        self.proc = subprocess.Popen(
            [command, *(args or [])], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8", env={**os.environ, **(env or {})}, bufsize=1,
        )
        self._id = 0
        self._lock = threading.Lock()

    def _request(self, method: str, params: dict | None = None) -> Any:
        with self._lock:
            self._id += 1
            mid = self._id
            self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "id": mid, "method": method, "params": params or {}}) + "\n")
            self.proc.stdin.flush()
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    raise RuntimeError(f"MCP server {self.name} closed the connection")
                msg = json.loads(line)
                if msg.get("id") == mid:
                    if "error" in msg:
                        raise RuntimeError(msg["error"].get("message", "MCP error"))
                    return msg.get("result")

    def _notify(self, method: str) -> None:
        self.proc.stdin.write(json.dumps({"jsonrpc": "2.0", "method": method}) + "\n")
        self.proc.stdin.flush()

    def start(self) -> list[dict]:
        self._request("initialize", {"protocolVersion": PROTOCOL_VERSION, "capabilities": {},
                                     "clientInfo": {"name": "factory-ai", "version": __version__}})
        self._notify("notifications/initialized")
        return self._request("tools/list").get("tools", [])

    def call(self, tool: str, args: dict) -> str:
        res = self._request("tools/call", {"name": tool, "arguments": args})
        parts = [c.get("text", "") for c in res.get("content", []) if c.get("type") == "text"]
        text = "\n".join(parts) or json.dumps(res)
        return ("ERROR: " + text) if res.get("isError") else text

    def close(self) -> None:
        try:
            self.proc.terminate()
        except Exception:
            pass


def needs_confirmation(tool: dict, server_read_only: bool) -> bool:
    """Safe by default: every external tool needs a human 'yes' unless it is
    declared read-only (by the server's annotations or in mcp.json) and its
    name does not look like an action."""
    name = tool.get("name", "").lower()
    looks_like_action = any(w in name for w in WRITE_WORDS)
    ann = tool.get("annotations") or {}
    declared_ro = server_read_only or ann.get("readOnlyHint") is True
    return looks_like_action or not declared_ro


CONFIRM: Callable[[str, dict], bool] = lambda name, args: False  # replaced by the CLI with an interactive prompt
CLIENTS: dict[str, MCPClient] = {}


def connect_servers(config_path: str | Path | None = None, log: Callable[[str], None] = lambda s: None) -> int:
    """Start configured MCP servers and register their tools. Returns number of tools added."""
    from .config import load
    from .tools import REGISTRY, Tool

    path = Path(config_path) if config_path else load().home / "mcp.json"
    if not path.exists():
        return 0
    cfg = json.loads(path.read_text(encoding="utf-8")).get("servers", {})
    added = 0
    for sname, sc in cfg.items():
        if sname in CLIENTS:
            continue
        try:
            client = MCPClient(sname, sc["command"], sc.get("args"), sc.get("env"))
            tools = client.start()
        except Exception as e:
            log(f"[mcp] {sname}: could not start ({e})")
            continue
        CLIENTS[sname] = client
        ro = bool(sc.get("read_only", False))
        for t in tools:
            full = f"{sname}__{t['name']}"
            confirm = needs_confirmation(t, ro)

            def make(client=client, tname=t["name"], full=full, confirm=confirm):
                def fn(**kwargs):
                    if confirm and not CONFIRM(full, kwargs):
                        return "Not executed: the engineer did not confirm this action."
                    return client.call(tname, kwargs)
                return fn

            desc = (t.get("description") or "").split("\n")[0][:300]
            if confirm:
                desc += " [requires engineer confirmation]"
            REGISTRY[full] = Tool(name=full, description=desc, func=make(),
                                  parameters=t.get("inputSchema") or {"type": "object", "properties": {}})
            added += 1
        log(f"[mcp] {sname}: {len(tools)} tools" + (" (read-only)" if ro else ""))
    return added


def close_all() -> None:
    for c in CLIENTS.values():
        c.close()
    CLIENTS.clear()
