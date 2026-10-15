"""The agent loop: local LLM + engineering tools + experience memory."""

from __future__ import annotations

import json
import re
from typing import Any, Callable

from .config import Config
from .knowledge import register_kb_tool
from .llm import OllamaClient
from .memory import default_memory
from .tools import REGISTRY, load_all

SYSTEM_PROMPT = """You are improvise, a production engineering assistant running locally.
You help design production lines, size machines, compute OEE/ROI, lay out lines and prepare
machine lists, part lists and manuals.

Rules:
- Never guess numbers. Use the calculation tools for takt time, capacity, machine count,
  line balance, OEE and ROI, and show the inputs you used.
- Before answering a design question, call recall_experience to check past cases and
  the engineer's confirmed rules; confirmed rules override general knowledge.
- Use search_knowledge for reference material and say which source you used.
- Leave prices you do not know blank; never invent prices or supplier data.
- When a job needs a program (simulation, data conversion, a chart, a custom calculation),
  write it with workspace_write, run it with run_python, read the output and fix errors.
  Keep scripts small and readable, standard library first.
- Answer in the user's language.
"""

FREE_SCOPE_NOTE = """
PLC control logic, IoT and production dashboards are part of Improvise Pro, which is not
installed. If asked for them, explain that briefly (see `improvise pro`) and still help with
the line design, calculations and documents that the request needs.
"""


class Agent:
    def __init__(self, cfg: Config, on_tool: Callable[[str, dict, Any], None] | None = None,
                 role_prompt: str = "", tool_names: list[str] | None = None, use_tools: bool = True):
        """role_prompt: extra instructions (e.g. a project-team role).
        tool_names: restrict the tools this agent may call (None = all).
        use_tools: False for pure reasoning/review steps."""
        self.cfg = cfg
        load_all()
        register_kb_tool()
        self.llm = OllamaClient(cfg.ollama_url, cfg.model, cfg.temperature, think=cfg.think)
        from .tools import PLUGINS
        prompt = SYSTEM_PROMPT + "".join(getattr(m, "PROMPT", "") for m in PLUGINS.values())
        if "pro" not in PLUGINS:
            prompt += FREE_SCOPE_NOTE
        from .skills import catalogue_prompt
        prompt += catalogue_prompt()
        if role_prompt:
            prompt += "\n" + role_prompt
        self.messages: list[dict] = [{"role": "system", "content": prompt}]
        self.on_tool = on_tool
        self.tool_names = tool_names
        self.use_tools = use_tools

    ALWAYS = ("use_skill", "recall_experience", "search_knowledge")

    def _select_tools(self, text: str) -> set[str]:
        """Small local models get confused by 30+ tools. Offer the ones that match the
        request (plus the always-on helpers); tools named by a loaded skill are added later."""
        if not self.use_tools:
            return set()
        names = [n for n in REGISTRY if self.tool_names is None or n in self.tool_names]
        limit = self.cfg.max_tools
        if self.tool_names is not None or len(names) <= limit:
            return set(names)
        words = {w for w in re.findall(r"[a-z]{3,}", text.lower())}
        words |= {w[:-1] for w in words if w.endswith("s")}

        def score(n: str) -> int:
            t = REGISTRY[n]
            hay = set(re.findall(r"[a-z]{3,}", (n.replace("_", " ") + " " + t.description).lower()))
            hay |= {w[:-1] for w in hay if w.endswith("s")}
            return len(words & hay)

        ranked = sorted((n for n in names if n not in self.ALWAYS), key=score, reverse=True)
        chosen = {n for n in ranked[: limit - len(self.ALWAYS)] if score(n) > 0}
        return chosen | {n for n in self.ALWAYS if n in names}

    def _schemas(self, allowed: set[str] | None = None) -> list[dict]:
        if not self.use_tools:
            return []
        return [t.schema() for n, t in REGISTRY.items() if (allowed is None and (self.tool_names is None or n in self.tool_names))
                or (allowed is not None and n in allowed)]

    def ask(self, text: str) -> str:
        experience = default_memory().context_for(text)
        content = text if not experience else f"{text}\n\n[Relevant experience]\n{experience}"
        self.messages.append({"role": "user", "content": content})
        allowed = self._select_tools(text)
        seen: dict[str, str] = {}

        for round_no in range(self.cfg.max_tool_rounds):
            last_round = round_no == self.cfg.max_tool_rounds - 1
            schemas = [] if last_round else self._schemas(allowed)
            if last_round:
                self.messages.append({"role": "user", "content": "Stop calling tools now and give your final answer "
                                      "from the results you already have."})
            msg = self.llm.chat(self.messages, tools=schemas or None)
            self.messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                return msg.get("content", "")
            for call in calls:
                fn = call.get("function", {})
                name, args = fn.get("name"), fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args or "{}")
                    except json.JSONDecodeError:
                        args = {}
                key = f"{name}:{json.dumps(args, sort_keys=True, default=str)}"
                tool = REGISTRY.get(name) if name in allowed else None
                if key in seen:
                    result = ("You already called this with the same arguments and got the result below. "
                              "Do not call it again - use it.\n" + seen[key])
                elif not tool:
                    result = f"Tool '{name}' is not available. Available: {', '.join(sorted(allowed))}"
                else:
                    try:
                        result = tool.call(args)
                    except Exception as e:  # tell the model exactly how to call it correctly
                        result = f"Tool error: {e}\nCorrect parameters: {json.dumps(tool.parameters, ensure_ascii=False)}"
                    if name == "use_skill":  # a loaded skill unlocks the tools it names
                        from .skills import load_skills
                        sk = load_skills().get(str(args.get("name", "")))
                        if sk:
                            allowed |= {t for t in sk.tools if t in REGISTRY}
                if self.on_tool:
                    self.on_tool(name, args, result)
                text_result = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
                seen.setdefault(key, text_result)
                self.messages.append({"role": "tool", "content": text_result})
        return "(stopped: too many tool rounds)"
