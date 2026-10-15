"""The agent loop: local LLM + engineering tools + experience memory."""

from __future__ import annotations

import json
from typing import Any, Callable

from .config import Config
from .knowledge import register_kb_tool
from .llm import OllamaClient
from .memory import default_memory
from .tools import REGISTRY, load_all

SYSTEM_PROMPT = """You are factory-ai, a production engineering assistant running locally.
You help design production lines, size machines, compute OEE/ROI, lay out lines and prepare
machine lists, part lists and manuals.

Rules:
- Never guess numbers. Use the calculation tools for takt time, capacity, machine count,
  line balance, OEE and ROI, and show the inputs you used.
- Before answering a design question, call recall_experience to check past cases and
  the engineer's confirmed rules; confirmed rules override general knowledge.
- Use search_knowledge for reference material and say which source you used.
- Leave prices you do not know blank; never invent prices or supplier data.
- Answer in the user's language.
"""

FREE_SCOPE_NOTE = """
PLC control logic, IoT and production dashboards are part of factory-ai Pro, which is not
installed. If asked for them, explain that briefly (see `factory-ai pro`) and still help with
the line design, calculations and documents that the request needs.
"""


class Agent:
    def __init__(self, cfg: Config, on_tool: Callable[[str, dict, Any], None] | None = None):
        self.cfg = cfg
        load_all()
        register_kb_tool()
        self.llm = OllamaClient(cfg.ollama_url, cfg.model, cfg.temperature)
        from .tools import PLUGINS
        prompt = SYSTEM_PROMPT + "".join(getattr(m, "PROMPT", "") for m in PLUGINS.values())
        if "pro" not in PLUGINS:
            prompt += FREE_SCOPE_NOTE
        self.messages: list[dict] = [{"role": "system", "content": prompt}]
        self.on_tool = on_tool

    def ask(self, text: str) -> str:
        experience = default_memory().context_for(text)
        content = text if not experience else f"{text}\n\n[Relevant experience]\n{experience}"
        self.messages.append({"role": "user", "content": content})
        schemas = [t.schema() for t in REGISTRY.values()]

        for _ in range(self.cfg.max_tool_rounds):
            msg = self.llm.chat(self.messages, tools=schemas)
            self.messages.append(msg)
            calls = msg.get("tool_calls") or []
            if not calls:
                return msg.get("content", "")
            for call in calls:
                fn = call.get("function", {})
                name, args = fn.get("name"), fn.get("arguments", {})
                tool = REGISTRY.get(name)
                try:
                    result = tool.call(args) if tool else f"Unknown tool {name}"
                except Exception as e:  # report tool errors back to the model
                    result = f"Tool error: {e}"
                if self.on_tool:
                    self.on_tool(name, args, result)
                self.messages.append({
                    "role": "tool",
                    "content": result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str),
                })
        return "(stopped: too many tool rounds)"
