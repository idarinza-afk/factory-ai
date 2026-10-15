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
- FLOWCHART FIRST: for a new process, machine sequence, control logic or workflow where the user has not
  given a flowchart, first draw one with make_flowchart, show it, and ask the user to approve or correct
  it. Only after approval write PLC code, programs or detailed documents.
- If ask_expert is available, use it for hard judgement questions (technology choice, troubleshooting
  ideas, design reviews); still compute every number with your own tools.
- When a job needs a program (simulation, data conversion, a chart, a custom calculation),
  write it with workspace_write, run it with run_python, read the output and fix errors.
  Keep scripts small and readable, standard library first.
- Answer in the language the user wrote in (Thai, English, Chinese, Japanese, Vietnamese, ...);
  keep units, tag names and code identifiers in their standard form.
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
        from .llm import make_client
        self.llm = make_client(cfg)
        from .tools import PLUGINS
        prompt = SYSTEM_PROMPT + "".join(getattr(m, "PROMPT", "") for m in PLUGINS.values())
        if "pro" not in PLUGINS:
            prompt += FREE_SCOPE_NOTE
        self.skill_hints = use_tools and (tool_names is None or "use_skill" in tool_names)
        if role_prompt:
            prompt += "\n" + role_prompt
        self.messages: list[dict] = [{"role": "system", "content": prompt}]
        self.on_tool = on_tool
        self.tool_names = tool_names
        self.use_tools = use_tools

    ALWAYS = ("use_skill", "recall_experience", "search_knowledge", "make_flowchart")

    def _select_tools(self, text: str) -> set[str]:
        """Small local models get confused by 30+ tools. Offer the ones that match the
        request (plus the always-on helpers); tools named by a loaded skill are added later."""
        if not self.use_tools:
            return set()
        names = [n for n in REGISTRY if self.tool_names is None or n in self.tool_names]
        limit = self.cfg.max_tools
        if self.tool_names is not None or len(names) <= limit:
            return set(names)
        from .lang import expand
        words = {w for w in re.findall(r"[a-z]{3,}", expand(text).lower())}
        words |= {w[:-1] for w in words if w.endswith("s")}

        def score(n: str) -> int:
            t = REGISTRY[n]
            hay = set(re.findall(r"[a-z]{3,}", (n.replace("_", " ") + " " + t.description).lower()))
            hay |= {w[:-1] for w in hay if w.endswith("s")}
            return len(words & hay)

        ranked = sorted((n for n in names if n not in self.ALWAYS), key=score, reverse=True)
        chosen = {n for n in ranked[: limit - len(self.ALWAYS)] if score(n) > 0}
        from .skills import relevant_skills
        for sk in relevant_skills(expand(text), limit=2):   # the best-matching skills bring their tools
            chosen |= {t for t in sk.tools if t in names}
        return chosen | {n for n in self.ALWAYS if n in names}

    @staticmethod
    def _numbers(text: str) -> set[float]:
        out = set()
        for m in re.findall(r"-?\d[\d,]*(?:\.\d+)?", text):
            try:
                out.add(round(float(m.replace(",", "")), 2))
            except ValueError:
                pass
        return out

    def _audit_numbers(self, answer: str, evidence: str) -> str | None:
        """Number audit: engineering figures in the answer must come from the user, a tool or the references."""
        have = self._numbers(evidence)
        def supported(v):
            return v in have or any(abs(v - h) <= max(0.02 * abs(h), 0.011) or abs(v - h * 100) <= 0.15
                                    or abs(v * 1000 - h) <= 0.6 or abs(v - h * 1000) <= 0.6 for h in have)
        claims = [v for v in self._numbers(answer) if abs(v) >= 3 and v not in (2024, 2025, 2026) and not supported(v)]
        if len(claims) >= 3:
            shown = ", ".join(f"{c:g}" for c in claims[:8])
            return (f"Number check: these figures are not from the user, a tool result or the references: {shown}. "
                    "Recompute them with the calculation tools, or clearly label them as assumptions/typical values. "
                    "Then give the corrected final answer.")
        return None

    def _guard(self, answer: str, called: set[str], allowed: set[str]) -> str | None:
        """Catch answers that hand-make what a tool must produce (e.g. ladder text without the generator).
        Guards come from plugins: GUARDS = [(regex, required_tool, message)]."""
        from .tools import PLUGINS
        for mod in PLUGINS.values():
            for pattern, tool, message in getattr(mod, "GUARDS", []):
                if tool in REGISTRY and tool not in called and re.search(pattern, answer, re.I | re.M):
                    allowed.add(tool)
                    return message
        return None

    def _schemas(self, allowed: set[str] | None = None) -> list[dict]:
        if not self.use_tools:
            return []
        return [t.schema() for n, t in REGISTRY.items() if (allowed is None and (self.tool_names is None or n in self.tool_names))
                or (allowed is not None and n in allowed)]

    LOGIC_WORDS = ("plc", "ladder", "sequence", "control logic", "interlock", "state machine", "flowchart", "workflow")
    APPROVAL_WORDS = ("approve", "approved", "อนุมัติ", "ถูกต้อง", "flowchart ok", "批准", "承認", "đồng ý")

    @staticmethod
    def detect_language(text: str) -> str:
        checks = [("Thai", 0x0E00, 0x0E7F), ("Japanese", 0x3040, 0x30FF), ("Korean", 0xAC00, 0xD7AF),
                  ("Chinese", 0x4E00, 0x9FFF), ("Vietnamese", 0x1EA0, 0x1EF9)]
        for name, a, b in checks:
            if any(a <= ord(c) <= b for c in text):
                return name
        return ""

    def ask(self, text: str) -> str:
        experience = default_memory().context_for(text)
        content = text if not experience else f"{text}\n\n[Relevant experience]\n{experience}"
        # small models rarely look things up on their own: attach the best reference passages
        from .knowledge import default_kb
        from .lang import expand
        refs = default_kb().search(expand(text), limit=2)
        lang = self.detect_language(text)
        if lang:
            content += f"\n\n[Reply in {lang}.]"
        from .lang import expand as _ex
        low = _ex(text).lower()
        if any(w in low for w in self.APPROVAL_WORDS):
            self.flow_approved = True
        if self.use_tools and not getattr(self, "flow_approved", False) and any(w in low for w in self.LOGIC_WORDS) \
                and "make_flowchart" in REGISTRY and (self.tool_names is None or "make_flowchart" in self.tool_names):
            content += ("\n\n[Rule: this involves control logic and no approved flowchart exists yet. Do the "
                        "calculations that are needed, then draw the sequence with make_flowchart, show it and ask the "
                        "user to approve it. Do NOT write PLC code in this answer.]")
        if self.skill_hints:
            from .skills import catalogue_prompt
            content += catalogue_prompt(expand(text))
        if refs:
            content += "\n\n[Reference knowledge - prefer this over general assumptions]\n" + "\n---\n".join(
                f"({src}) {body[:900]}" for src, body in refs)
        self.messages.append({"role": "user", "content": content})
        allowed = self._select_tools(text)
        called_tools: set[str] = set()
        guard_retries = 0
        reports: list[str] = []   # tool output that must reach the user verbatim (generated code, verdicts, files)
        if "make_flowchart" in REGISTRY and self.use_tools and self.tool_names is None:
            allowed.add("make_flowchart")
        if self.cfg.expert_provider and self.use_tools and self.tool_names is None:
            allowed.add("ask_expert")  # a second brain is configured
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
                answer = msg.get("content", "")
                fix = None if last_round else self._guard(answer, called_tools, allowed)
                if not answer.strip() and not last_round:  # small models sometimes stop with an empty reply
                    fix = ("Your reply was empty. Continue the task: call the tools you still need (convert per-shift or "
                           "per-day figures to per-hour first if needed), then give the final answer.")
                if not fix and not last_round and called_tools and self.cfg.number_audit:
                    evidence = "\n".join(str(m.get("content", "")) for m in self.messages if m.get("role") in ("user", "tool"))
                    fix = self._audit_numbers(answer, evidence)
                if not fix and reports:
                    answer = answer.rstrip() + "\n\n---\n" + "\n\n".join(dict.fromkeys(reports))
                if fix and guard_retries < 2:
                    guard_retries += 1
                    self.messages.append({"role": "user", "content": fix})
                    continue
                return answer
            for ci, call in enumerate(calls):
                call.setdefault("id", f"call_{round_no}_{ci}")
                fn = call.get("function", {})
                name, args = fn.get("name"), fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args or "{}")
                    except json.JSONDecodeError:
                        args = {}
                called_tools.add(name)
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
                if isinstance(result, dict):
                    if result.get("report_to_user"):
                        reports.append(str(result["report_to_user"]))
                    files = [str(v) for k, v in result.items() if isinstance(v, str)
                             and re.search(r"\.(xlsx|csv|docx|md|svg|html|dxf|obj|json|st|txt|ino|mmd)$", v, re.I)]
                    if files:
                        reports.append("Files: " + ", ".join(files))
                if self.on_tool:
                    self.on_tool(name, args, result)
                text_result = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
                seen.setdefault(key, text_result)
                self.messages.append({"role": "tool", "content": text_result, "tool_call_id": call["id"]})
        return "(stopped: too many tool rounds)"
