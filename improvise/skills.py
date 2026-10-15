"""Skills: packaged know-how the model loads only when a job needs it.

A skill is a folder with a SKILL.md:

    ---
    name: conveyor-design
    description: Size a conveyor - speed, belt pull, motor power. Use for any conveyor question.
    tools: conveyor_sizing, workspace_write
    ---
    step-by-step method, rules of thumb, checks, output format...

Sources (later ones override earlier ones with the same name):
  improvise/skill_library/        built-in skills
  plugins (SKILLS_DIR)            e.g. Improvise Pro
  ~/.improvise/skills/            your own skills

The model sees a one-line catalogue of all skills in its system prompt and calls
use_skill(name) to read the full instructions - so hundreds of skills cost almost
nothing until one is needed.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .tools import tool

BUILTIN = Path(__file__).parent / "skill_library"


@dataclass
class Skill:
    name: str
    description: str
    body: str
    path: Path
    tools: list[str]


def _parse(path: Path) -> Skill | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", text, re.S)
    if not m:
        return None
    meta: dict[str, str] = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    if "name" not in meta:
        return None
    tools = [t.strip() for t in meta.get("tools", "").split(",") if t.strip()]
    return Skill(meta["name"], meta.get("description", ""), m.group(2).strip(), path, tools)


def skill_dirs() -> list[Path]:
    from .config import load
    from .tools import load_plugins
    dirs = [BUILTIN]
    dirs += [Path(m.SKILLS_DIR) for m in load_plugins().values() if getattr(m, "SKILLS_DIR", None)]
    dirs.append(load().home / "skills")
    return dirs


def load_skills() -> dict[str, Skill]:
    skills: dict[str, Skill] = {}
    for d in skill_dirs():
        if not d.exists():
            continue
        for f in sorted(d.glob("*/SKILL.md")):
            s = _parse(f)
            if s:
                skills[s.name] = s
    return skills


def relevant_skills(query: str, limit: int = 6) -> list[Skill]:
    """Skills whose name/description share the most words with the request."""
    words = set(re.findall(r"[a-z]{3,}", query.lower()))
    words |= {w[:-1] for w in words if w.endswith("s")}

    def score(s: Skill) -> int:
        hay = set(re.findall(r"[a-z]{3,}", (s.name.replace("-", " ") + " " + s.description).lower()))
        hay |= {w[:-1] for w in hay if w.endswith("s")}
        return len(words & hay)

    ranked = sorted(load_skills().values(), key=score, reverse=True)
    return [s for s in ranked[:limit] if score(s) > 0]


def catalogue_prompt(query: str | None = None, limit: int = 6) -> str:
    """With a query: the few skills relevant to it. Without: the full catalogue."""
    skills = relevant_skills(query, limit) if query else list(load_skills().values())
    if not skills:  # e.g. a request in Thai: give just the names, cheap to read
        names = sorted(load_skills())
        return ("\nSKILLS available (call use_skill(name) when one fits): " + ", ".join(names) + "\n") if names else ""
    lines = "\n".join(f"- {s.name}: {s.description}" for s in skills)
    return ("\nSKILLS - if the job matches one of these, call use_skill(name) first and follow it:\n"
            + lines + "\n")


@tool
def use_skill(name: str) -> str:
    """Load the full instructions of a skill (see the SKILLS list in your instructions).

    Args:
        name: skill name, e.g. conveyor-design
    """
    skills = load_skills()
    s = skills.get(name) or skills.get(name.strip().lower().replace(" ", "-"))
    if not s:
        return "Unknown skill. Available: " + ", ".join(sorted(skills))
    extra = f"\n\n(Tools this skill uses: {', '.join(s.tools)})" if s.tools else ""
    return f"# Skill: {s.name}\n\n{s.body}{extra}"


TEMPLATE = """---
name: {name}
description: <one line - what it does and WHEN to use it>
tools: <comma-separated tool names, optional>
---
## Goal
<what a good result looks like>

## Method
1. <step>
2. <step>

## Checks
- <what to verify before answering>

## Output
<format of the answer / files to produce>
"""


def new_skill(name: str) -> Path:
    from .config import load
    slug = re.sub(r"[^a-z0-9-]+", "-", name.lower()).strip("-")
    d = load().home / "skills" / slug
    d.mkdir(parents=True, exist_ok=True)
    f = d / "SKILL.md"
    if not f.exists():
        f.write_text(TEMPLATE.format(name=slug), encoding="utf-8")
    return f
