"""Project team mode - you talk only to the Project Manager.

1. You describe the project to the Project Manager (PM).
2. The PM proposes a team for it: positions from the role catalogue plus new
   positions the project needs.
3. YOU define every position: keep the PM's description, write your own
   responsibilities, rename, add or remove positions, choose their tools.
4. From then on you keep talking to the PM. For each request the PM delegates
   to the team members, they work with only their own tools on a shared project
   board, the consultant (if on the team) reviews, and the PM answers you.

Teams are saved per project in ~/.improvise/teams/<project>.json and can be
reopened. The role catalogue is team_roles.json (+ ~/.improvise/team_roles.json).
Roles marked "pro" are only offered when Improvise Pro is installed.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROLES_FILE = Path(__file__).parent / "team_roles.json"
LEAD_KEY = "project_manager"


def load_roles() -> dict[str, dict]:
    """The role catalogue (built-in + user's), filtered to what is installed."""
    from .config import load
    from .tools import load_plugins
    roles = json.loads(ROLES_FILE.read_text(encoding="utf-8"))
    user = load().home / "team_roles.json"
    if user.exists():
        roles.update(json.loads(user.read_text(encoding="utf-8")))
    pro = "pro" in load_plugins()
    return {k: v for k, v in roles.items() if pro or not v.get("pro")}


def available_tools() -> list[str]:
    from .knowledge import register_kb_tool
    from .tools import REGISTRY, load_all
    load_all()
    register_kb_tool()
    return sorted(n for n in REGISTRY if "__" not in n and n != "save_case")


def slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")[:40] or "member"


def role_prompt(role: dict) -> str:
    return (f"You are the {role['title']} in a production-line project team.\n"
            f"Your responsibility, as defined by the project owner: {role['focus']}\n"
            "Work only within your responsibility, use your tools for every number, state assumptions, "
            "and end with 'Open questions:' listing information you still need. Be concise.")


def _json_in(text: str, open_ch: str, close_ch: str):
    m = re.search(re.escape(open_ch) + r".*" + re.escape(close_ch), text, re.S)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        return None


@dataclass
class ProjectTeam:
    project: str
    members: dict[str, dict] = field(default_factory=dict)   # key -> {title, focus, tools, reviewer?}
    brief: str = ""
    board: list[dict] = field(default_factory=list)         # {who, title, task, output, time}
    pm_history: list[dict] = field(default_factory=list)    # PM conversation with the user
    _on_tool: Any = field(default=None, repr=False, compare=False)
    _current_calls: Any = field(default=None, repr=False, compare=False)

    def _record(self, name, args, result):
        if self._current_calls is not None:
            r = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
            self._current_calls.append(f"{name} -> {r[:300]}")
        if self._on_tool:
            self._on_tool(name, args, result)

    # ---------------------------------------------------------------- persistence
    @staticmethod
    def path_for(project: str) -> Path:
        from .config import load
        d = load().home / "teams"
        d.mkdir(parents=True, exist_ok=True)
        return d / f"{slug(project)}.json"

    def save(self) -> Path:
        p = self.path_for(self.project)
        p.write_text(json.dumps({"project": self.project, "brief": self.brief, "members": self.members,
                                 "board": self.board[-60:], "pm_history": self.pm_history[-40:]},
                                ensure_ascii=False, indent=2), encoding="utf-8")
        return p

    @classmethod
    def load(cls, project: str) -> "ProjectTeam | None":
        p = cls.path_for(project)
        if not p.exists():
            return None
        d = json.loads(p.read_text(encoding="utf-8"))
        return cls(d["project"], d.get("members", {}), d.get("brief", ""), d.get("board", []), d.get("pm_history", []))

    @staticmethod
    def list_projects() -> list[str]:
        from .config import load
        d = load().home / "teams"
        return sorted(p.stem for p in d.glob("*.json")) if d.exists() else []

    # ---------------------------------------------------------------- team editing (by the user)
    def set_member(self, key: str, title: str | None = None, focus: str | None = None,
                   tools: list[str] | None = None, reviewer: bool | None = None) -> dict:
        key = slug(key)
        if key == LEAD_KEY:
            raise ValueError("the Project Manager is who you talk to, not a team member")
        m = self.members.setdefault(key, {"title": title or key.replace("_", " ").title(), "focus": "", "tools": []})
        if title is not None:
            m["title"] = title
        if focus is not None:
            m["focus"] = focus
        if tools is not None:
            valid = set(available_tools())
            m["tools"] = [t for t in tools if t in valid]
        if reviewer is not None:
            m["reviewer"] = reviewer
        return m

    def remove_member(self, key: str) -> bool:
        return self.members.pop(slug(key), None) is not None

    def describe(self) -> str:
        if not self.members:
            return "(no team members yet)"
        lines = []
        for k, m in self.members.items():
            tag = " [reviewer]" if m.get("reviewer") else ""
            lines.append(f"- {k}: {m['title']}{tag}\n    responsibility: {m['focus'] or '(not defined)'}\n"
                         f"    tools: {', '.join(m.get('tools') or []) or '(none - reasoning only)'}")
        return "\n".join(lines)

    # ---------------------------------------------------------------- LLM helpers
    def _agent(self, role_text: str, tools: list[str] | None, use_tools: bool, cfg, client, member: dict | None = None):
        from dataclasses import replace
        from .agent import Agent
        from .config import _env
        # a position can run on its own model, e.g. a coder model for the Software Engineer
        model = (member or {}).get("model") or (_env((member or {}).get("model_env", "")) if (member or {}).get("model_env") else None)
        mcfg = replace(cfg, max_tool_rounds=min(cfg.max_tool_rounds, 5))  # keep each member's turn short
        if model:
            mcfg = replace(mcfg, model=model)
        a = Agent(mcfg, role_prompt=role_text, tool_names=tools, use_tools=use_tools, on_tool=self._record)
        if client is not None:
            a.llm = client
        return a

    def _pm_prompt(self) -> str:
        return ("You are the Project Manager of this production-line project and the ONLY person the project "
                "owner talks to. You lead a team whose members and responsibilities were defined by the owner:\n"
                f"{self.describe()}\n"
                "Delegate work to the members, never do a member's calculations yourself, report results clearly, "
                "and ask the owner when a decision or missing information is needed. If the owner has not given a "
                "process flow or workflow, have one drawn as a flowchart first and get the owner's approval before "
                "detailed design, documents or control logic.")

    def propose(self, brief: str, cfg=None, client=None) -> dict[str, dict]:
        """PM suggests positions for the project. Nothing is applied until the user accepts."""
        from .config import load
        cfg = cfg or load()
        self.brief = brief
        catalogue = {k: {"title": v["title"], "focus": v["focus"]} for k, v in load_roles().items() if k != LEAD_KEY}
        tools = available_tools()
        pm = self._agent("You are the Project Manager of a production-line project.", None, False, cfg, client)
        text = pm.ask(
            "Which positions does this project need? Pick keys from the catalogue and, only if really needed, "
            "add new positions. Keep it short.\nCATALOGUE: " + ", ".join(f"{k} ({v['title']})" for k, v in catalogue.items())
            + '\nReply ONLY with JSON: {"existing": ["key", ...], "new": [{"title": "...", "focus": "one sentence"}]}'
            + f"\n\nBRIEF:\n{brief}")
        raw_obj = _json_in(text, "{", "}") or {}
        raw: dict = {}
        if isinstance(raw_obj.get("existing"), list) or isinstance(raw_obj.get("new"), list):
            for k in raw_obj.get("existing") or []:
                raw[str(k)] = {}
            for n in raw_obj.get("new") or []:
                if isinstance(n, dict) and n.get("title"):
                    raw[slug(n["title"])] = {"title": n["title"], "focus": n.get("focus", ""), "tools": n.get("tools", [])}
        else:  # older/other answer shape: {"key": {...}}
            raw = raw_obj
        cat = load_roles()
        proposal: dict[str, dict] = {}
        for key, val in raw.items():
            if not isinstance(val, dict):
                continue
            k = slug(key)
            if k == LEAD_KEY:
                continue
            base = cat.get(k, {})
            proposal[k] = {
                **({"model_env": base["model_env"]} if base.get("model_env") else {}),
                "title": val.get("title") or base.get("title") or k.replace("_", " ").title(),
                "focus": val.get("focus") or base.get("focus", ""),
                "tools": [t for t in (base.get("tools") or val.get("tools") or []) if t in tools],
            }
            if base.get("reviewer"):
                proposal[k]["reviewer"] = True
        if not proposal:  # model gave nothing usable: offer the standard team
            proposal = {k: {"title": v["title"], "focus": v["focus"], "tools": [t for t in v.get("tools", []) if t in tools],
                            **({"reviewer": True} if v.get("reviewer") else {})}
                        for k, v in cat.items() if k != LEAD_KEY}
        return proposal

    def work(self, request: str, cfg=None, client=None, progress: Callable[[str], None] = lambda s: None) -> str:
        """The owner talks to the PM; the PM delegates, collects, and replies."""
        from .config import load
        cfg = cfg or load()
        if not self.members:
            return "The team is empty - define at least one team member first."
        workers = {k: m for k, m in self.members.items() if not m.get("reviewer")}
        reviewers = {k: m for k, m in self.members.items() if m.get("reviewer")}

        pm = self._agent(self._pm_prompt(), None, False, cfg, client)
        pm.messages += self.pm_history[-12:]
        plan_text = pm.ask(
            f"The owner says:\n{request}\n\nDecide who on the team does what. Reply with a JSON list like "
            '[{"member": "<key>", "task": "..."}] using only these keys: ' + json.dumps(list(workers)) +
            ". Reply [] if you can answer without the team.")
        plan = [p for p in (_json_in(plan_text, "[", "]") or [])
                if isinstance(p, dict) and p.get("member") in workers]

        board_ctx = self._board_text()
        for step in plan:
            m = workers[step["member"]]
            progress(f"  [{m['title']}] {str(step.get('task', ''))[:80]}")
            agent = self._agent(role_prompt(m), m.get("tools") or [], bool(m.get("tools")), cfg, client, m)
            calls: list[str] = []
            self._current_calls = calls
            out = agent.ask(f"{board_ctx}\n\nOWNER REQUEST:\n{request}\n\nYOUR TASK FROM THE PM:\n{step.get('task', '')}")
            if calls:  # facts the PM can rely on: what was actually computed or produced
                out += "\n\n[Tool record] " + "; ".join(calls)
            self.board.append({"who": step["member"], "title": m["title"], "task": step.get("task", ""),
                               "output": out, "time": time.strftime("%Y-%m-%d %H:%M")})
            board_ctx = self._board_text()

        if plan:
            for k, m in reviewers.items():
                progress(f"  [{m['title']}] reviewing")
                agent = self._agent(role_prompt(m), m.get("tools") or [], bool(m.get("tools")), cfg, client)
                out = agent.ask(f"{board_ctx}\n\nReview the latest work for the owner's request: {request}\n"
                                "Check in this order and say PASS or FAIL for each:\n"
                                "1. Units: was the demand read correctly (per hour vs per day vs per shift)?\n"
                                "2. Capacity: is the line output (after OEE) >= the required rate? Name the bottleneck.\n"
                                "3. Is every number backed by a [Tool record]? Flag numbers that are not.\n"
                                "4. Were any prices, model numbers, suppliers or power ratings invented?\n"
                                "5. Do the documents claimed (drawings, 3D, lists) actually exist in a [Tool record]?\n"
                                "Then list what must change before this goes to the customer.")
                self.board.append({"who": k, "title": m["title"], "task": "review", "output": out,
                                   "time": time.strftime("%Y-%m-%d %H:%M")})
            board_ctx = self._board_text()

        progress("  [Project Manager] reporting")
        reply = pm.ask(f"{board_ctx}\n\nReport back to the owner on: {request}\n"
                       "Use only numbers backed by a [Tool record], name who did what, include every FAIL from the "
                       "review as an open issue, never claim a drawing or document exists unless a [Tool record] shows "
                       "the file, and list decisions needed and next steps.")
        self.pm_history += [{"role": "user", "content": request}, {"role": "assistant", "content": reply}]
        self.save()
        return reply

    def _board_text(self, last: int = 5, limit: int = 900) -> str:
        parts = [f"PROJECT: {self.project}\nBRIEF: {self.brief}"]
        for e in self.board[-last:]:
            parts.append(f"--- {e['title']} ({e['task']}):\n{e['output'][:limit]}")
        return "\n\n".join(parts)

    def report_markdown(self) -> str:
        md = [f"# {self.project} - project team report\n\n**Brief:** {self.brief}\n\n## Team\n\n{self.describe()}\n"]
        for e in self.board:
            md.append(f"## {e['title']} — {e['time']}\n\n*Task:* {e['task']}\n\n{e['output']}\n")
        return "\n".join(md)


# backwards-compatible one-shot run (non-interactive): PM proposes, team accepted as proposed
def run_team(brief: str, cfg=None, only: list[str] | None = None, client=None,
             progress: Callable[[str], None] = lambda s: None, project: str | None = None,
             on_tool=None) -> dict[str, Any]:
    t = ProjectTeam(project or f"project_{time.strftime('%Y%m%d_%H%M%S')}")
    t._on_tool = on_tool
    t.brief = brief
    if only:  # positions chosen by the user: take them straight from the catalogue
        cat, tools = load_roles(), set(available_tools())
        for k in list(only) + [k for k, v in cat.items() if v.get("reviewer")]:
            if k in cat and k != LEAD_KEY:
                v = cat[k]
                t.members[k] = {"title": v["title"], "focus": v["focus"], "tools": [x for x in v.get("tools", []) if x in tools],
                                **({"reviewer": True} if v.get("reviewer") else {}),
                                **({"model_env": v["model_env"]} if v.get("model_env") else {})}
    else:
        progress("[Project Manager] proposing the team")
        t.members = t.propose(brief, cfg, client)
    summary = t.work(brief, cfg, client, progress)
    from .config import load
    path = (cfg or load()).output_dir / f"{slug(t.project)}_team_report.md"
    path.write_text(t.report_markdown(), encoding="utf-8")
    return {"report": str(path), "members": t.members, "summary": summary, "entries": t.board}
