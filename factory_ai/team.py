"""Project team mode: the AI splits its thinking into a project team.

    Project Manager  -> plans: which specialists do what
    Specialists      -> each works with only the tools of their discipline,
                        reading the shared project board (earlier results)
    Consultant       -> independent review: risks, inconsistencies, gaps
    Project Manager  -> final summary: decisions, open questions, next steps

Roles live in team_roles.json. Add or override roles in
~/.factory-ai/team_roles.json (same format), e.g. a "packaging_specialist".
Roles marked "pro" join only when factory-ai Pro is installed.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

ROLES_FILE = Path(__file__).parent / "team_roles.json"


def load_roles() -> dict[str, dict]:
    from .config import load
    from .tools import load_plugins
    roles = json.loads(ROLES_FILE.read_text(encoding="utf-8"))
    user = load().home / "team_roles.json"
    if user.exists():
        roles.update(json.loads(user.read_text(encoding="utf-8")))
    pro = "pro" in load_plugins()
    return {k: v for k, v in roles.items() if pro or not v.get("pro")}


def role_prompt(key: str, role: dict) -> str:
    return (f"You are the {role['title']} in a production-line project team.\n"
            f"Your responsibility: {role['focus']}\n"
            "Work only within your discipline, use your tools for every number, state assumptions, "
            "and end with 'Open questions:' listing information you still need. Be concise.")


@dataclass
class Board:
    brief: str
    entries: list[dict] = field(default_factory=list)

    def add(self, role: str, title: str, task: str, output: str) -> None:
        self.entries.append({"role": role, "title": title, "task": task, "output": output})

    def text(self, limit: int = 1800) -> str:
        parts = [f"PROJECT BRIEF:\n{self.brief}"]
        for e in self.entries:
            parts.append(f"--- {e['title']} ({e['task']}):\n{e['output'][:limit]}")
        return "\n\n".join(parts)

    def markdown(self) -> str:
        md = [f"# Project team report\n\n**Brief:** {self.brief}\n"]
        for e in self.entries:
            md.append(f"## {e['title']}\n\n*Task:* {e['task']}\n\n{e['output']}\n")
        return "\n".join(md)


def _parse_plan(text: str, roles: dict[str, dict]) -> list[dict]:
    m = re.search(r"\[.*\]", text, re.S)
    plan: list[dict] = []
    if m:
        try:
            for item in json.loads(m.group(0)):
                if isinstance(item, dict) and item.get("role") in roles and not roles[item["role"]].get("lead") \
                        and not roles[item["role"]].get("reviewer"):
                    plan.append({"role": item["role"], "task": str(item.get("task", ""))})
        except json.JSONDecodeError:
            pass
    if not plan:  # fallback: every specialist does their standard part
        plan = [{"role": k, "task": "Do your discipline's part for this brief."}
                for k, r in roles.items() if not r.get("lead") and not r.get("reviewer")]
    return plan


def run_team(brief: str, cfg=None, only: list[str] | None = None, client=None,
             progress: Callable[[str], None] = lambda s: None) -> dict[str, Any]:
    from .agent import Agent
    from .config import load

    cfg = cfg or load()
    roles = load_roles()
    if only:
        keep = set(only) | {k for k, r in roles.items() if r.get("lead") or r.get("reviewer")}
        roles = {k: v for k, v in roles.items() if k in keep}
    lead = next(k for k, r in roles.items() if r.get("lead"))
    reviewer = next((k for k, r in roles.items() if r.get("reviewer")), None)
    board = Board(brief)

    def agent_for(key: str, use_tools: bool = True) -> Agent:
        a = Agent(cfg, role_prompt=role_prompt(key, roles[key]), tool_names=roles[key].get("tools"), use_tools=use_tools)
        if client is not None:
            a.llm = client
        return a

    # 1. plan
    specialists = {k: r["title"] for k, r in roles.items() if not r.get("lead") and not r.get("reviewer")}
    progress(f"[{roles[lead]['title']}] planning")
    plan_text = agent_for(lead, use_tools=False).ask(
        "Plan the work for this brief. Choose only the specialists that are needed from: "
        + json.dumps(specialists) + "\nReply with a JSON list like "
        '[{"role": "process_engineer", "task": "..."}] in the order the work should be done.\n\n'
        f"BRIEF:\n{brief}")
    plan = _parse_plan(plan_text, roles)
    board.add(lead, roles[lead]["title"] + " - plan", "plan the work",
              "\n".join(f"{i}. {roles[p['role']]['title']}: {p['task']}" for i, p in enumerate(plan, 1)))

    # 2. specialists
    for step in plan:
        key = step["role"]
        progress(f"[{roles[key]['title']}] {step['task'][:70]}")
        out = agent_for(key).ask(f"{board.text()}\n\nYOUR TASK:\n{step['task']}")
        board.add(key, roles[key]["title"], step["task"], out)

    # 3. review
    if reviewer:
        progress(f"[{roles[reviewer]['title']}] reviewing")
        out = agent_for(reviewer).ask(
            f"{board.text()}\n\nReview the team's work. List: 1) inconsistencies between disciplines, "
            "2) risks, 3) missing information, 4) what must change before this goes to the customer.")
        board.add(reviewer, roles[reviewer]["title"], "independent review", out)

    # 4. summary
    progress(f"[{roles[lead]['title']}] summarising")
    summary = agent_for(lead, use_tools=False).ask(
        f"{board.text()}\n\nWrite the project summary for the customer and the team: scope, key numbers "
        "(only those the team computed), decisions, open questions, next steps.")
    board.add(lead, roles[lead]["title"] + " - summary", "project summary", summary)

    out_dir = cfg.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"team_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
    path.write_text(board.markdown(), encoding="utf-8")
    return {"report": str(path), "plan": plan, "summary": summary, "entries": board.entries}
