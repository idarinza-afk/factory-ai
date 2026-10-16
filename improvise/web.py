"""Local web screen for Improvise: `improvise ui`.

Standard library only (works offline on a factory PC). The server listens on 127.0.0.1
only, and every API call must carry the session token that is embedded in the page, so
other web sites open in the same browser cannot drive the assistant.

Screen: chat with the assistant (tool steps shown live), previews of the files it makes
(2D/3D/electrical drawings, flowcharts, lists, PLC code), approval prompts for actions
that change something, and the engineer's rules (memory).
"""

from __future__ import annotations

import json
import mimetypes
import secrets
import threading
import time
import uuid
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from . import __version__

PAGE = Path(__file__).with_name("web_ui.html")
PREVIEW_EXT = {".svg", ".html", ".htm", ".png", ".jpg", ".jpeg", ".gif", ".csv", ".md", ".txt", ".st", ".ino",
               ".mmd", ".json", ".scl", ".log"}


def _short(obj, n: int = 160) -> str:
    s = obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, default=str)
    return s if len(s) <= n else s[: n - 1] + "…"


class Session:
    """One conversation with the assistant plus the jobs (questions) running in it."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.lock = threading.Lock()   # one question at a time per conversation
        self.jobs: dict[str, dict] = {}
        self.pending: dict[str, dict] = {}   # approvals waiting for the engineer
        self.last_q = self.last_a = ""
        self.agent = None
        self.current: dict | None = None

    def _agent(self):
        if self.agent is None:
            from .agent import Agent
            self.agent = Agent(self.cfg, on_tool=self._on_tool)
        return self.agent

    def reset(self) -> None:
        with self.lock:
            self.agent = None
            self.last_q = self.last_a = ""

    # ---- events shown live in the page
    def _event(self, kind: str, **data) -> None:
        if self.current is not None:
            self.current["events"].append({"kind": kind, "t": round(time.time() - self.current["started"], 1), **data})

    def _on_tool(self, name, args, result) -> None:
        err = isinstance(result, str) and result.startswith(("Tool error", "Tool '"))
        files = []
        if isinstance(result, dict):
            files = [v for v in result.values() if isinstance(v, str) and Path(v).suffix and Path(v).is_absolute()]
        self._event("tool", name=name, args=_short(args), ok=not err, summary=_short(result, 220), files=files)

    def confirm(self, name: str, args: dict) -> bool:
        """Called by improvise.safety before any action that changes something: ask in the page."""
        cid = uuid.uuid4().hex[:10]
        ev = threading.Event()
        self.pending[cid] = {"name": name, "args": _short(args, 600), "event": ev, "allow": False}
        self._event("confirm", id=cid, name=name, args=_short(args, 600))
        ev.wait(timeout=300)  # no answer in 5 minutes = no
        item = self.pending.pop(cid, {})
        self._event("confirmed", id=cid, allow=bool(item.get("allow")))
        return bool(item.get("allow"))

    def answer_confirm(self, cid: str, allow: bool) -> bool:
        item = self.pending.get(cid)
        if not item:
            return False
        item["allow"] = allow
        item["event"].set()
        return True

    def ask(self, text: str) -> str:
        job = {"id": uuid.uuid4().hex[:10], "question": text, "events": [], "done": False, "answer": "",
               "error": "", "started": time.time()}
        self.jobs[job["id"]] = job

        def run():
            from .llm import LLMError
            with self.lock:
                self.current = job
                try:
                    job["answer"] = self._agent().ask(text)
                    self.last_q, self.last_a = text, job["answer"]
                except LLMError as e:
                    job["error"] = str(e)
                except Exception as e:  # keep the screen alive, show what happened
                    job["error"] = f"{type(e).__name__}: {e}"
                finally:
                    job["seconds"] = round(time.time() - job["started"], 1)
                    job["done"] = True
                    self.current = None

        threading.Thread(target=run, daemon=True).start()
        return job["id"]


def _files(roots: list[Path], limit: int = 200) -> list[dict]:
    out = []
    for root in roots:
        if not root.exists():
            continue
        for f in root.rglob("*"):
            rel = f.relative_to(root)
            if f.is_file() and ".history" not in rel.parts:
                st = f.stat()
                out.append({"name": rel.as_posix(), "root": root.name, "size": st.st_size, "mtime": st.st_mtime,
                            "preview": f.suffix.lower() in PREVIEW_EXT, "path": str(f)})
    out.sort(key=lambda x: x["mtime"], reverse=True)
    return out[:limit]


def make_handler(session: Session, token: str, roots: dict[str, Path]):
    page = PAGE.read_text(encoding="utf-8").replace("%TOKEN%", token).replace("%VERSION%", __version__)

    class H(BaseHTTPRequestHandler):
        server_version = "improvise"

        def log_message(self, *a):  # quiet console
            pass

        def _send(self, code: int, body: bytes, ctype: str, extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code: int = 200):
            self._send(code, json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8"),
                       "application/json; charset=utf-8")

        def _host_ok(self) -> bool:
            # blocks DNS-rebinding: a foreign site name pointed at 127.0.0.1 must not read the page
            host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]")
            if host in ("127.0.0.1", "localhost", "::1"):
                return True
            self._json({"error": "open the screen at http://127.0.0.1"}, 403)
            return False

        def _authorised(self) -> bool:
            if not self._host_ok():
                return False
            q = parse_qs(urlparse(self.path).query)
            if self.headers.get("X-Improvise-Token") == token or q.get("token", [""])[0] == token:
                return True
            self._json({"error": "missing or wrong session token"}, 403)
            return False

        def _body(self) -> dict:
            n = int(self.headers.get("Content-Length") or 0)
            if n > 2_000_000:
                raise ValueError("request too large")
            return json.loads(self.rfile.read(n) or b"{}")

        def _serve_file(self, rel: str):
            root_name, _, name = rel.partition("/")
            root = roots.get(root_name)
            if not root:
                return self._json({"error": "unknown folder"}, 404)
            p = (root / unquote(name)).resolve()
            if root.resolve() not in p.parents or not p.is_file():
                return self._json({"error": "not found"}, 404)
            ctype = mimetypes.guess_type(p.name)[0] or "application/octet-stream"
            if p.suffix.lower() in {".st", ".ino", ".mmd", ".md", ".csv", ".log", ".scl", ".txt"}:
                ctype = "text/plain; charset=utf-8"
            extra = {}
            if p.suffix.lower() not in PREVIEW_EXT:
                extra["Content-Disposition"] = f'attachment; filename="{p.name}"'
            self._send(200, p.read_bytes(), ctype, extra)

        # ---------------- GET
        def do_GET(self):
            u = urlparse(self.path)
            if u.path in ("/", "/index.html"):
                if not self._host_ok():
                    return
                return self._send(200, page.encode("utf-8"), "text/html; charset=utf-8")
            if not self._authorised():
                return
            if u.path == "/api/status":
                return self._json(_status(session.cfg))
            if u.path == "/api/files":
                return self._json(_files(list(roots.values())))
            if u.path.startswith("/api/job/"):
                job = session.jobs.get(u.path.rsplit("/", 1)[-1])
                if not job:
                    return self._json({"error": "unknown job"}, 404)
                since = int(parse_qs(u.query).get("since", ["0"])[0])
                return self._json({**{k: v for k, v in job.items() if k != "events"},
                                   "events": job["events"][since:], "next": len(job["events"]),
                                   "elapsed": round(time.time() - job["started"], 1)})
            if u.path == "/api/rules":
                from .memory import default_memory
                return self._json(default_memory().list_feedback())
            if u.path.startswith("/files/"):
                return self._serve_file(u.path[len("/files/"):])
            self._json({"error": "not found"}, 404)

        # ---------------- POST
        def do_POST(self):
            if not self._authorised():
                return
            u = urlparse(self.path)
            try:
                b = self._body()
            except (ValueError, json.JSONDecodeError) as e:
                return self._json({"error": str(e)}, 400)
            from .memory import default_memory
            if u.path == "/api/ask":
                text = str(b.get("text", "")).strip()
                if not text:
                    return self._json({"error": "empty question"}, 400)
                if session.lock.locked():
                    return self._json({"error": "still working on the previous question"}, 409)
                return self._json({"job": session.ask(text)})
            if u.path == "/api/confirm":
                ok = session.answer_confirm(str(b.get("id", "")), bool(b.get("allow")))
                return self._json({"ok": ok})
            if u.path == "/api/reset":
                if session.lock.locked():
                    return self._json({"error": "wait until the current answer is finished"}, 409)
                session.reset()
                return self._json({"ok": True})
            if u.path == "/api/rules":
                topic, rule = str(b.get("topic", "")).strip(), str(b.get("rule", "")).strip()
                if not rule:
                    return self._json({"error": "rule is empty"}, 400)
                return self._json({"id": default_memory().add_feedback(topic or "general", rule)})
            if u.path == "/api/rules/delete":
                return self._json({"ok": default_memory().delete_feedback(int(b.get("id", 0)))})
            if u.path == "/api/save":
                if not session.last_a:
                    return self._json({"error": "nothing to save yet"}, 400)
                cid = default_memory().add_case(str(b.get("kind") or "other"), str(b.get("title") or session.last_q[:60]),
                                                session.last_q, session.last_a)
                return self._json({"id": cid})
            self._json({"error": "not found"}, 404)

    return H


def _status(cfg) -> dict:
    from .memory import default_memory
    from .tools import PLUGINS, REGISTRY, load_all
    load_all()
    try:
        from .skills import load_skills
        n_skills = len(load_skills())
    except Exception:
        n_skills = 0
    return {"version": __version__, "provider": cfg.provider, "model": cfg.model,
            "expert": f"{cfg.expert_provider} / {cfg.expert_model or cfg.model}" if cfg.expert_provider else "",
            "tools": len(REGISTRY), "skills": n_skills, "plugins": sorted(PLUGINS), "pro": "pro" in PLUGINS,
            "memory": default_memory().stats(), "output_dir": str(cfg.output_dir)}


def serve(port: int = 8765, open_browser: bool = True) -> None:
    from . import mcp, safety
    from .config import load
    cfg = load()
    cfg.ensure_dirs()
    session = Session(cfg)
    safety.CONFIRM = session.confirm
    try:
        mcp.connect_servers(log=lambda m: print(m))
    except Exception as e:
        print(f"(MCP connectors skipped: {e})")
    from .coding import workspace
    roots = {"output": cfg.output_dir, "workspace": workspace()}
    token = secrets.token_urlsafe(18)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), make_handler(session, token, roots))
    url = f"http://127.0.0.1:{port}/"
    print(f"Improvise {__version__} screen: {url}   (Ctrl+C to stop)")
    print(f"brain: {cfg.provider} / {cfg.model}")
    if open_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("stopped")
    finally:
        httpd.server_close()
