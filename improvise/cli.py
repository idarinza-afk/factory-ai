"""Command line interface.

  improvise chat                         interactive assistant (needs Ollama)
  improvise ask "question"               one-shot question
  improvise tools                        list engineering tools
  improvise run <tool> '<json args>'     run a tool directly, no LLM needed
  improvise memory add|verify|rule|search|stats|export
  improvise pro                          what the Pro edition adds
  improvise bench [--model m] [--compare old.json]   score a model on engineering questions
  improvise team [--project name]        talk to your Project Manager, who builds and leads a team
  improvise team "brief..." | team --list
  improvise ingest <manual.pdf | folder>  read machine manuals into local knowledge
  improvise connect [list | add <name> | remove <name>]  plug into FreeCAD, Excel, Grafana, OPC UA...
  improvise backup [list | restore <zip>]        your data, backed up daily automatically
  improvise selftest | update [--rollback]       safe self-update that rolls back if broken
  improvise skills [show <name> | new <name>]   packaged know-how loaded on demand
  improvise mcp serve | mcp tools        MCP server for other AIs / list tools from ~/.improvise/mcp.json
  improvise contribute [--secret "Customer A" ...]
  improvise doctor                       check the local setup
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

    from . import mcp

    def confirm(name, a):
        if not sys.stdin.isatty():
            return False
        print(f"\n  ! {name} wants to run with {json.dumps(a, ensure_ascii=False)[:300]}")
        return input("    allow this action? [y/N] ").strip().lower() == "y"

    from . import safety
    safety.CONFIRM = confirm
    mcp.connect_servers(log=lambda m: print(m, file=sys.stderr))
    agent = Agent(load(), on_tool=show if args.verbose else None)
    if args.question:
        try:
            print(agent.ask(" ".join(args.question)))
        except LLMError as e:
            sys.exit(str(e))
        return
    print("improvise - type 'exit' to quit, '/save' to save the last answer as a case")
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
            print(f"saved as case #{cid}. Verify it later with: improvise memory verify {cid} \"site result\"")
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
        sys.exit(f"unknown tool {args.tool}. See: improvise tools")
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
    elif args.action == "rules":
        for r in m.list_feedback():
            print(f"#{r['id']:<4} [{r['topic']}] {r['rule']}")
    elif args.action == "delrule":
        print("deleted" if m.delete_feedback(args.id) else "no such rule")
    elif args.action == "export":
        n = m.export_finetune(args.out, only_verified=not args.all)
        print(f"wrote {n} training records to {args.out}")


PRO_INFO = """Improvise Pro (coming soon) - for control and automation work

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
        print("Improvise Pro is installed. Run 'improvise tools' to see the Pro tools.")
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


def cmd_bench(args) -> None:
    from . import bench
    items = bench.load_items(args.file)
    if args.only:
        items = [i for i in items if i["id"].startswith(args.only) or i.get("category") == args.only]
    if args.limit:
        items = items[: args.limit]
    res = bench.run(model=args.model, items=items, progress=lambda m: print(m, flush=True))
    from .config import load
    out = Path(args.out) if args.out else load().output_dir / f"bench_{res['model'].replace(':', '-').replace('/', '-')}_{res['date'][:10]}.json"
    out.write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nscore {res['score']:.3f} on {res['items']} items  {res['by_category']}")
    print(f"saved {out}")
    if args.compare:
        print()
        print(bench.compare(res, json.loads(Path(args.compare).read_text(encoding="utf-8"))))


TEAM_HELP = """You are talking to the Project Manager. Commands:
  /team                 show the team and each position's responsibility
  /role <key>           define or change a position (title, responsibility, tools)
  /add <title>          add a new position
  /remove <key>         remove a position
  /reviewer <key>       make a position the reviewer (or turn it off)
  /tools                list tools you can give to positions
  /board                show the team's latest work
  /report               save the full team report (Markdown)
  /help                 this help
  exit                  leave (the project is saved)"""


def _edit_role(team, key, proposal=None) -> None:
    from .team import available_tools
    cur = team.members.get(key) or (proposal or {}).get(key) or {}
    title = input(f"  title [{cur.get('title', key)}]: ").strip() or cur.get("title", key)
    print(f"  current responsibility: {cur.get('focus') or '(none)'}")
    focus = input("  responsibility (Enter = keep): ").strip() or cur.get("focus", "")
    tools_now = ", ".join(cur.get("tools") or [])
    t = input(f"  tools [{tools_now or 'none'}] (comma list, Enter = keep, '?' = list): ").strip()
    if t == "?":
        print("  " + ", ".join(available_tools()))
        t = input("  tools: ").strip()
    tools = [x.strip() for x in t.split(",") if x.strip()] if t else list(cur.get("tools") or [])
    team.set_member(key, title, focus, tools, cur.get("reviewer"))


def cmd_team(args) -> None:
    from .llm import LLMError
    from .team import ProjectTeam, load_roles, run_team, slug, available_tools
    if args.list:
        for k, r in load_roles().items():
            tag = " (you talk to this one)" if r.get("lead") else " (reviewer)" if r.get("reviewer") else " [Pro]" if r.get("pro") else ""
            print(f"{k:22s} {r['title']}{tag}")
        print("\nRole catalogue. Add your own in ~/.improvise/team_roles.json. Saved projects: "
              + (", ".join(ProjectTeam.list_projects()) or "none"))
        return
    if args.brief:  # one-shot, non-interactive
        only = [r.strip() for r in args.roles.split(",")] if args.roles else None
        try:
            show = (lambda n, a, r: print(f"      [tool] {n}({json.dumps(a, ensure_ascii=False)[:110]})", flush=True)) if args.verbose else None
            res = run_team(" ".join(args.brief), only=only, progress=lambda m: print(m, flush=True), on_tool=show)
        except LLMError as e:
            sys.exit(str(e))
        print("\n" + res["summary"] + f"\n\nfull team report: {res['report']}")
        return

    # interactive: the owner only talks to the Project Manager
    projects = ProjectTeam.list_projects()
    if projects:
        print("saved projects: " + ", ".join(projects))
    name = (args.project or input("project name: ").strip() or "my_project")
    team = ProjectTeam.load(name)
    try:
        if team:
            print(f"\nPM: Welcome back to '{team.project}'. The team:\n{team.describe()}")
        else:
            team = ProjectTeam(name)
            brief = input("\nPM: Hello, I am your Project Manager. Tell me about the project:\n> ").strip()
            print("\nPM: Let me propose a team...")
            proposal = team.propose(brief)
            for k, m in proposal.items():
                print(f"\n  {m['title']} ({k}){' [reviewer]' if m.get('reviewer') else ''}\n    {m['focus']}")
            print("\nPM: Please define each position. For each: Enter = accept as proposed, e = edit, n = not needed.")
            for k, m in proposal.items():
                ans = input(f"  {m['title']} [Enter/e/n]: ").strip().lower()
                if ans == "n":
                    continue
                if ans == "e":
                    _edit_role(team, k, proposal)
                else:
                    team.set_member(k, m["title"], m["focus"], m.get("tools"), m.get("reviewer"))
            while input("\nPM: Add another position? [y/N] ").strip().lower() == "y":
                title = input("  title: ").strip()
                if title:
                    _edit_role(team, slug(title), {slug(title): {"title": title}})
            team.save()
            print(f"\nPM: The team is set:\n{team.describe()}\n\nWhat should we work on first?")
        print("(type /help for commands)")
        while True:
            try:
                q = input("\nyou> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not q:
                continue
            if q in ("exit", "quit"):
                break
            cmd, _, arg = q.partition(" ")
            if cmd == "/help":
                print(TEAM_HELP)
            elif cmd == "/team":
                print(team.describe())
            elif cmd == "/role" and arg:
                _edit_role(team, slug(arg)); team.save()
            elif cmd == "/add" and arg:
                _edit_role(team, slug(arg), {slug(arg): {"title": arg}}); team.save()
            elif cmd == "/remove" and arg:
                print("removed" if team.remove_member(arg) else "no such position"); team.save()
            elif cmd == "/reviewer" and arg:
                m = team.members.get(slug(arg))
                if m:
                    m["reviewer"] = not m.get("reviewer"); team.save()
                    print(f"{m['title']} reviewer: {m['reviewer']}")
            elif cmd == "/tools":
                print(", ".join(available_tools()))
            elif cmd == "/board":
                for e in team.board[-5:]:
                    print(f"\n--- {e['title']} ({e['task']})\n{e['output'][:1200]}")
            elif cmd == "/report":
                from .config import load
                p = load().output_dir / f"{slug(team.project)}_team_report.md"
                p.write_text(team.report_markdown(), encoding="utf-8")
                print(f"saved {p}")
            elif cmd.startswith("/"):
                print(TEAM_HELP)
            else:
                print("PM: on it...")
                print("\nPM: " + team.work(q, progress=print))
    except LLMError as e:
        print(e)
    finally:
        if team:
            team.save()


def cmd_ingest(args) -> None:
    from .manuals import ingest
    for r in ingest(args.path, args.name):
        _print(r)


def cmd_connect(args) -> None:
    from . import connectors as c
    if args.action == "add":
        kv = lambda items: dict(i.split("=", 1) for i in items or [])  # noqa: E731
        _print(c.add(args.name, kv(args.param), kv(args.env)))
    elif args.action == "remove":
        print("removed" if c.remove(args.name) else "not connected")
    else:
        inst = c.installed()
        cat = None
        for name, e in sorted(c.CATALOGUE.items(), key=lambda kv: (kv[1]["category"], kv[0])):
            if e["category"] != cat:
                cat = e["category"]
                print(f"\n{cat}")
            print(f"  {'[x]' if name in inst else '[ ]'} {name:11s} {e['about']}")
        print(f"\nconfig: {c.config_path()}  - then 'improvise mcp tools' to see the connected tools")


def cmd_backup(args) -> None:
    from . import guard
    if args.action == "restore":
        if not args.file:
            sys.exit("give the backup file: improvise backup restore <zip>")
        print(f"current state saved to {guard.restore(args.file)}; backup restored")
    elif args.action == "list":
        for f in guard.list_backups():
            print(f"{f.name}  {f.stat().st_size // 1024} KB")
    else:
        print(f"backup written: {guard.backup()}")


def cmd_selftest(args) -> None:
    from .guard import selftest
    r = selftest()
    if not args.quiet:
        _print(r)
    sys.exit(0 if r["ok"] else 1)


def cmd_update(args) -> None:
    from . import guard
    ok = guard.rollback() if args.rollback else guard.update()
    sys.exit(0 if ok else 1)


def cmd_skills(args) -> None:
    from .skills import load_skills, new_skill, skill_dirs, use_skill
    if args.action == "show" and args.name:
        print(use_skill(args.name))
    elif args.action == "new" and args.name:
        print(f"created {new_skill(args.name)} - edit it, it is picked up automatically")
    else:
        for s in load_skills().values():
            print(f"{s.name:30s} {s.description[:95]}")
        print("\nskill folders: " + ", ".join(str(d) for d in skill_dirs()))


def cmd_mcp(args) -> None:
    from . import mcp
    if args.action == "serve":
        mcp.serve()
    elif args.action == "tools":
        n = mcp.connect_servers(log=print)
        from .tools import REGISTRY
        for name, t in sorted(REGISTRY.items()):
            if "__" in name:
                print(f"{name:40s} {t.description[:90]}")
        print(f"{n} external tools" if n else "no MCP servers configured (see ~/.improvise/mcp.json)")
        mcp.close_all()


def cmd_doctor(args) -> None:
    import urllib.request
    from .config import load
    cfg = load()
    print(f"home     : {cfg.home}")
    print(f"brain    : {cfg.provider} / {cfg.model}" + (f"  (API {cfg.api_base})" if cfg.api_base else ""))
    print(f"expert   : {cfg.expert_provider + ' / ' + (cfg.expert_model or cfg.model) if cfg.expert_provider else 'not configured'}")
    if cfg.provider != "ollama":
        print(f"api key  : {'set' if cfg.api_key else 'MISSING (IMPROVISE_API_KEY)'}")
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
    p = argparse.ArgumentParser(prog="improvise", description="Local AI for production engineering")
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
    ms.add_parser("rules")
    x = ms.add_parser("delrule")
    x.add_argument("id", type=int)
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
    sub.add_parser("pro", help="what Improvise Pro adds").set_defaults(func=cmd_pro)

    tm = sub.add_parser("team", help="work on a brief as a project team (PM, consultant, engineers...)")
    tm.add_argument("brief", nargs="*", help="give a brief for a one-shot run; omit to talk to the PM interactively")
    tm.add_argument("--project", help="project name (interactive mode)")
    tm.add_argument("--roles", help="one-shot: keep only these positions, e.g. process_engineer,design_engineer")
    tm.add_argument("--list", action="store_true", help="list the role catalogue and saved projects")
    tm.add_argument("-v", "--verbose", action="store_true", help="show tool calls")
    tm.set_defaults(func=cmd_team)

    ig = sub.add_parser("ingest", help="read machine manuals (PDF/TXT/MD file or folder) into local knowledge")
    ig.add_argument("path")
    ig.add_argument("--name", help="machine / manual name")
    ig.set_defaults(func=cmd_ingest)

    cn = sub.add_parser("connect", help="plug Improvise into other software (FreeCAD, Excel, Grafana, OPC UA...)")
    cn.add_argument("action", nargs="?", choices=["list", "add", "remove"], default="list")
    cn.add_argument("name", nargs="?")
    cn.add_argument("--param", action="append", help="key=value, e.g. dir=C:/quotes")
    cn.add_argument("--env", action="append", help="KEY=VALUE stored only in your local mcp.json")
    cn.set_defaults(func=cmd_connect)

    bk = sub.add_parser("backup", help="back up / restore your experience, skills and teams")
    bk.add_argument("action", nargs="?", choices=["create", "list", "restore"], default="create")
    bk.add_argument("file", nargs="?")
    bk.set_defaults(func=cmd_backup)
    st = sub.add_parser("selftest", help="check that the program works")
    st.add_argument("--quiet", action="store_true")
    st.set_defaults(func=cmd_selftest)
    up = sub.add_parser("update", help="safe self-update from GitHub with automatic rollback")
    up.add_argument("--rollback", action="store_true", help="return to the last working version")
    up.set_defaults(func=cmd_update)

    sk = sub.add_parser("skills", help="list, show or create skills")
    sk.add_argument("action", nargs="?", choices=["list", "show", "new"], default="list")
    sk.add_argument("name", nargs="?")
    sk.set_defaults(func=cmd_skills)

    mc = sub.add_parser("mcp", help="MCP: serve improvise to other AIs, or list connected MCP tools")
    mc.add_argument("action", choices=["serve", "tools"])
    mc.set_defaults(func=cmd_mcp)

    b = sub.add_parser("bench", help="benchmark the current model on engineering questions")
    b.add_argument("--model", help="Ollama model to test (default: IMPROVISE_MODEL)")
    b.add_argument("--file", help="custom benchmark JSONL")
    b.add_argument("--only", help="item id prefix or category")
    b.add_argument("--limit", type=int)
    b.add_argument("--out", help="where to save the results JSON")
    b.add_argument("--compare", help="previous results JSON to compare against")
    b.set_defaults(func=cmd_bench)

    from .tools import load_plugins
    for mod in load_plugins().values():
        if hasattr(mod, "register_cli"):
            mod.register_cli(sub)

    args = p.parse_args(argv)
    if args.cmd in ("chat", "ask", "team"):
        try:
            from .guard import auto_backup
            auto_backup()
        except Exception:
            pass  # a backup problem must never block work
    args.func(args)


if __name__ == "__main__":
    main()
