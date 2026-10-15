"""Command line interface.

  factory-ai chat                         interactive assistant (needs Ollama)
  factory-ai ask "question"               one-shot question
  factory-ai tools                        list engineering tools
  factory-ai run <tool> '<json args>'     run a tool directly, no LLM needed
  factory-ai memory add|verify|rule|search|stats|export
  factory-ai pro                          what the Pro edition adds
  factory-ai contribute [--secret "Customer A" ...]
  factory-ai doctor                       check the local setup
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _print(obj) -> None:
    if isinstance(obj, str):
        print(obj)
    else:
        print(json.dumps(obj, indent=2, ensure_ascii=False, default=str))


def cmd_chat(args) -> None:
    from .agent import Agent
    from .config import load
    from .llm import LLMError

    def show(name, a, r):
        print(f"  [tool] {name}({json.dumps(a, ensure_ascii=False)[:120]})", file=sys.stderr)

    agent = Agent(load(), on_tool=show if args.verbose else None)
    if args.question:
        try:
            print(agent.ask(" ".join(args.question)))
        except LLMError as e:
            sys.exit(str(e))
        return
    print("factory-ai - type 'exit' to quit, '/save' to save the last answer as a case")
    last_q = last_a = ""
    while True:
        try:
            q = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if q in {"exit", "quit"}:
            break
        if q == "/save" and last_a:
            from .memory import default_memory
            title = input("title: ").strip() or last_q[:60]
            kind = input("kind (line_design/machine_list/plc/iot/roi/other): ").strip() or "other"
            cid = default_memory().add_case(kind, title, last_q, last_a)
            print(f"saved as case #{cid}. Verify it later with: factory-ai memory verify {cid} \"site result\"")
            continue
        if not q:
            continue
        try:
            last_a = agent.ask(q)
            last_q = q
            print(last_a)
        except LLMError as e:
            print(e)


def cmd_tools(args) -> None:
    from .knowledge import register_kb_tool
    from .tools import load_all
    reg = load_all()
    register_kb_tool()
    for name, t in sorted(reg.items()):
        print(f"{name:28s} {t.description}")


def cmd_run(args) -> None:
    from .knowledge import register_kb_tool
    from .tools import load_all
    reg = load_all()
    register_kb_tool()
    if args.tool not in reg:
        sys.exit(f"unknown tool {args.tool}. See: factory-ai tools")
    raw = args.args
    if raw and Path(raw).exists():
        raw = Path(raw).read_text(encoding="utf-8")
    _print(reg[args.tool].call(json.loads(raw or "{}")))


def cmd_memory(args) -> None:
    from .memory import default_memory
    m = default_memory()
    if args.action == "add":
        cid = m.add_case(args.kind, args.title, args.problem, args.solution, args.outcome or "", bool(args.outcome))
        print(f"case #{cid}")
    elif args.action == "verify":
        m.update_outcome(args.id, args.outcome, True)
        print(f"case #{args.id} verified")
    elif args.action == "rule":
        print(f"rule #{m.add_feedback(args.topic, args.rule)}")
    elif args.action == "search":
        _print(m.context_for(args.query) or "nothing found")
    elif args.action == "stats":
        _print(m.stats())
    elif args.action == "export":
        n = m.export_finetune(args.out, only_verified=not args.all)
        print(f"wrote {n} training records to {args.out}")


PRO_INFO = """factory-ai Pro (coming soon) - for control and automation work

  PLC control logic   I/O list, sequence -> IEC 61131-3 Structured Text, standard
                      function blocks, static check, simulator test loop,
                      exporters for Siemens TIA, Mitsubishi GX Works, Omron Sysmac
  IoT                 MQTT / OPC UA tag maps, read-only edge collectors,
                      gateway configuration
  Dashboards          OEE and production dashboards built from your lines' data,
                      downtime and reject analysis, shift reports

Pricing (prices to be announced):
  Pro          monthly subscription per user
  Team         monthly subscription per seat, shared experience memory
  Enterprise   annual licence, on-prem install, fine-tuning on company data, support

Interested? Open an issue on GitHub with the label 'pro-interest'.
"""


def cmd_pro(args) -> None:
    from .tools import load_plugins
    if "pro" in load_plugins():
        print("factory-ai Pro is installed. Run 'factory-ai tools' to see the Pro tools.")
    else:
        print(PRO_INFO)


def cmd_contribute(args) -> None:
    from .config import load
    from .contribute import build_pack
    from .memory import default_memory

    def ask(rec: dict) -> bool:
        if args.yes:
            return True
        print("\n" + "=" * 70)
        _print(rec)
        return input("share this record? [y/N] ").strip().lower() == "y"

    out = args.out or str(load().output_dir / "contribution.jsonl")
    res = build_pack(default_memory(), out, secret_terms=args.secret, approve=ask, contributor=args.name)
    _print(res)
    print("\nNext: open a Pull Request adding this file to the community dataset repo (see CONTRIBUTING.md).")


def cmd_doctor(args) -> None:
    import urllib.request
    from .config import load
    cfg = load()
    print(f"home     : {cfg.home}")
    print(f"model    : {cfg.model}")
    try:
        with urllib.request.urlopen(f"{cfg.ollama_url}/api/tags", timeout=5) as r:
            models = [m["name"] for m in json.loads(r.read()).get("models", [])]
        print(f"ollama   : OK ({len(models)} models)")
        if cfg.model not in models:
            print(f"           model not pulled yet -> ollama pull {cfg.model}")
    except Exception:
        print(f"ollama   : NOT reachable at {cfg.ollama_url} (install from https://ollama.com)")
    for mod in ("openpyxl", "docx"):
        try:
            __import__(mod)
            print(f"{mod:9s}: installed")
        except ImportError:
            print(f"{mod:9s}: not installed (optional)")


def main(argv: list[str] | None = None) -> None:
    p = argparse.ArgumentParser(prog="factory-ai", description="Local AI for production engineering")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("chat", help="interactive assistant")
    c.add_argument("question", nargs="*")
    c.add_argument("-v", "--verbose", action="store_true")
    c.set_defaults(func=cmd_chat)
    a = sub.add_parser("ask", help="one-shot question")
    a.add_argument("question", nargs="+")
    a.add_argument("-v", "--verbose", action="store_true")
    a.set_defaults(func=cmd_chat)

    sub.add_parser("tools", help="list tools").set_defaults(func=cmd_tools)
    r = sub.add_parser("run", help="run a tool directly")
    r.add_argument("tool")
    r.add_argument("args", nargs="?", default="{}", help="JSON string or path to a JSON file")
    r.set_defaults(func=cmd_run)

    m = sub.add_parser("memory", help="experience memory")
    ms = m.add_subparsers(dest="action", required=True)
    x = ms.add_parser("add")
    x.add_argument("--kind", default="other")
    x.add_argument("--title", required=True)
    x.add_argument("--problem", required=True)
    x.add_argument("--solution", required=True)
    x.add_argument("--outcome")
    x = ms.add_parser("verify")
    x.add_argument("id", type=int)
    x.add_argument("outcome")
    x = ms.add_parser("rule")
    x.add_argument("topic")
    x.add_argument("rule")
    x = ms.add_parser("search")
    x.add_argument("query")
    ms.add_parser("stats")
    x = ms.add_parser("export")
    x.add_argument("out")
    x.add_argument("--all", action="store_true", help="include unverified cases")
    m.set_defaults(func=cmd_memory)

    co = sub.add_parser("contribute", help="build an anonymised contribution pack")
    co.add_argument("--secret", action="append", default=[], help="extra term to redact (repeatable)")
    co.add_argument("--name", default="anonymous", help="contributor name shown in the pack")
    co.add_argument("--out")
    co.add_argument("--yes", action="store_true", help="accept all records without asking")
    co.set_defaults(func=cmd_contribute)

    sub.add_parser("doctor", help="check setup").set_defaults(func=cmd_doctor)
    sub.add_parser("pro", help="what factory-ai Pro adds").set_defaults(func=cmd_pro)

    from .tools import load_plugins
    for mod in load_plugins().values():
        if hasattr(mod, "register_cli"):
            mod.register_cli(sub)

    args = p.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
