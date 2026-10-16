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
- If an input is missing but the tool has a sensible default (material, efficiency, service factor, pressure...),
  use the default, state it as an assumption and give the result. Ask only when no reasonable default exists
  (e.g. the production rate or demand).
- If find_machine_model is available, the engineer's own machine designs are connected: look machines up there
  (sizes, pass line, connections, clearances) before assuming dimensions, and give layout_line their model_id.
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
                    "Recompute them with the calculation tools, or label them as assumptions/typical values. Then write "
                    "the complete final answer again for the user - do not mention this check.")
        return None

    # The question asks for something a tool must produce: (regex on the question, tool, needs numbers in the question)
    REQUIRED_TOOLS = [
        (r"receiver|ถังพักลม|ถังลม|储气罐|エアタンク|bình chứa khí", "air_receiver", True),
        (r"electrical (diagram|schematic|drawing)|wiring diagram|ไดอะแกรมไฟฟ้า|วงจรไฟฟ้า|แบบไฟฟ้า|电气图|電気図|sơ đồ điện",
         "electrical_schematic", False),
        (r"\boee\b", "oee", True),
        (r"model library|from (our|the|my) library|in the library|คลังโมเดล|จากคลัง|ในคลัง", "find_machine_model", False),
        (r"shaft diameter|đường kính trục|เส้นผ่าน(ศูนย์กลาง)?เพลา|ขนาดเพลา|轴径|軸径", "shaft_diameter", True),
        (r"\bcpk?\b", "process_capability", True),
        (r"line balanc|workstations|สมดุลไลน์", "line_balance", True),
        (r"\bdxf\b|2d (layout )?drawing|แบบ 2d|2d layout", "layout_dxf", False),
        (r"3d model|โมเดล 3d|\b3d\b.*(view|model|layout)", "layout_3d", False),
    ]
    # The key result of each tool: an answer that called the tool must use one of these values
    HEADLINES = {
        "takt_time": ["takt_time_s"], "takt_from_rate": ["takt_time_s_per_unit", "takt_time_s_per_pack"],
        "oee": ["oee"], "machines_required": ["machines"], "line_balance": ["workstations"],
        "air_receiver": ["receiver_volume_L", "suggested_size_L"],
        "batch_heat_up": ["heating_power_kW", "steam_kg_per_h_during_heat_up"],
        "pump_power": ["selected_motor_kW", "required_motor_kW"], "shaft_diameter": ["min_diameter_mm", "suggested_diameter_mm"],
        "drive_torque": ["output_torque_Nm", "design_torque_Nm"], "roi": ["payback_years", "npv"],
        "process_capability": ["Cpk"], "pipe_size": ["nominal_size_DN", "required_inside_diameter_mm"],
        "conveyor_sizing": ["selected_motor_kW"], "heat_load": ["heat_load_kW"], "cooling_load": ["design_load_kW"],
        "buffer_size": ["buffer_units"], "staffing": ["total_headcount"],
        "pneumatic_cylinder": ["machine_total_air_NL_min", "air_NL_per_min_all_cylinders", "suggested_standard_bore_mm"],
        "product_spacing": ["outfeed_speed_m_per_min", "speed_ratio"],
        "utilities_summary": ["transformer_kVA_min", "compressed_air_NL_min"],
    }

    def _unused_results(self, answer: str, results: dict) -> str | None:
        found = self._numbers(answer)

        def near(v: float) -> bool:
            return any(abs(v - h) <= max(0.02 * abs(v), 0.011) or abs(v * 100 - h) <= max(0.02 * abs(v * 100), 0.15)
                       or abs(v / 1000 - h) <= 0.02 * abs(v / 1000) + 0.001 for h in found)
        for tool, outs in results.items():
            keys = self.HEADLINES.get(tool)
            if not keys:
                continue
            vals = [(k, o[k]) for o in outs for k in keys
                    if isinstance(o.get(k), (int, float)) and not isinstance(o.get(k), bool)]
            if vals and not any(near(float(v)) for _, v in vals):
                shown = ", ".join(f"{k} = {v}" for k, v in vals[:4])
                return (f"Your answer does not use the result of {tool} ({shown}). Do not recompute by hand: write the "
                        "complete final answer again using the tool results (call the tool again with corrected "
                        "inputs only if they were wrong). Do not mention this check.")
        return None

    BREAK_WORDS = r"break|meal|lunch|พัก|休憩|休息|nghỉ|istirahat|휴식|pause"
    # (tool, argument that must be set when the question mentions it, regex on the question, note)
    ARG_CHECKS = [
        ("oee", "planned_breaks_min", BREAK_WORDS,
         "The question mentions planned breaks but planned_breaks_min is 0: call oee again with planned_breaks_min "
         "(planned_time_min = the whole shift)."),
        ("takt_time", "break_min_per_shift", BREAK_WORDS,
         "The question mentions breaks but break_min_per_shift is 0: call takt_time again with break_min_per_shift."),
        ("takt_from_rate", "break_min_per_shift", BREAK_WORDS + r"|per shift|ต่อกะ",
         "If the shift has breaks, set break_min_per_shift (and shifts/hours_per_shift) and call again."),
    ]

    def _arg_warning(self, name: str, args: dict) -> str | None:
        q = getattr(self, "_question", "")
        for tool, arg, pattern, note in self.ARG_CHECKS:
            if name == tool and not args.get(arg) and re.search(pattern, q, re.I):
                if tool == "takt_from_rate" and not args.get("hours_per_shift"):
                    continue  # a pure rate question: breaks do not matter
                return note
        return None

    PROMISE = re.compile(r"\b(I will now|I'll now|let'?s proceed|let me now|next,? I will|I will (now )?(create|draw|generate|make)"
                         r"|let me (adjust|fix|correct|update|try again|re-?run|simulate again)|I'?ll (adjust|fix|correct) (this|it|the))\b"
                         r"|จะดำเนินการ|ต่อไปจะ(สร้าง|วาด|ทำ)", re.I)

    def _required_tool(self, called: set[str], allowed: set[str]) -> str | None:
        q = getattr(self, "_question", "")
        if not q or not self.use_tools:
            return None
        from .tools import PLUGINS
        rules = list(self.REQUIRED_TOOLS) + [r for m in PLUGINS.values() for r in getattr(m, "REQUIRED_TOOLS", [])]
        for pattern, tool, needs_numbers in rules:
            if tool not in REGISTRY or tool in called or (self.tool_names is not None and tool not in self.tool_names):
                continue
            if tool.startswith("plc_generate") and not getattr(self, "flow_approved", False):
                continue  # no PLC code before the flowchart is approved
            if re.search(pattern, q, re.I) and (not needs_numbers or re.search(r"\d", q)):
                allowed.add(tool)
                return (f"The request needs {tool} - call it now with the user's figures (do not work it out by hand "
                        "or skip it), then write the complete final answer.")
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
        self._question = low
        allowed = self._select_tools(text)
        called_tools: set[str] = set()
        guard_retries = 0
        reports: list[str] = []   # tool output that must reach the user verbatim (generated code, verdicts, files)
        if "make_flowchart" in REGISTRY and self.use_tools and self.tool_names is None:
            allowed.add("make_flowchart")
        try:
            from .model_library import library_dir
            if library_dir() and self.use_tools:  # the engineer's own machine designs are connected
                for t in ("find_machine_model", "machine_model_details"):
                    if t in REGISTRY and (self.tool_names is None or t in self.tool_names):
                        allowed.add(t)
        except Exception:
            pass
        if self.cfg.expert_provider and self.use_tools and self.tool_names is None:
            allowed.add("ask_expert")  # a second brain is configured
        seen: dict[str, str] = {}
        tool_results: dict[str, list] = {}

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
                fix = None if last_round else (self._required_tool(called_tools, allowed)
                                               or self._guard(answer, called_tools, allowed))
                if not fix and not last_round and self.PROMISE.search(answer[-600:]):
                    fix = ("You said you would do more but stopped. Do it now with the tools, then write the complete "
                           "final answer (include everything from before).")
                if not answer.strip() and not last_round:  # small models sometimes stop with an empty reply
                    fix = ("Your reply was empty. Continue the task: call the tools you still need (convert per-shift or "
                           "per-day figures to per-hour first if needed), then give the final answer.")
                if not fix and not last_round and tool_results:
                    fix = self._unused_results(answer, tool_results)
                if not fix and not last_round and called_tools and self.cfg.number_audit:
                    evidence = "\n".join(str(m.get("content", "")) for m in self.messages if m.get("role") in ("user", "tool"))
                    fix = self._audit_numbers(answer, evidence)
                if not fix and reports:
                    answer = answer.rstrip() + "\n\n---\n" + "\n\n".join(dict.fromkeys(reports))
                if fix and guard_retries < 3:
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
                if isinstance(result, dict) and tool:
                    warn = self._arg_warning(name, args if isinstance(args, dict) else {})
                    if warn:
                        result = {**result, "input_warning": warn}
                    tool_results.setdefault(name, []).append(result)
                if self.on_tool:
                    self.on_tool(name, args, result)
                text_result = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False, default=str)
                seen.setdefault(key, text_result)
                self.messages.append({"role": "tool", "content": text_result, "tool_call_id": call["id"]})
        return "(stopped: too many tool rounds)"
