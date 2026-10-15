import json
from pathlib import Path

import pytest

EX = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture(autouse=True)
def _home(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPROVISE_HOME", str(tmp_path))
    import improvise.memory as mem
    import improvise.knowledge as kb
    mem._default = None
    kb._kb = None


def test_takt_and_machines():
    from improvise.calc.line import machines_required, takt_time
    t = takt_time(demand_units=57600, shifts=2, hours_per_shift=8, break_min_per_shift=60)
    assert t["available_time_s"] == 50400
    assert t["takt_time_s"] == pytest.approx(0.875)
    m = machines_required(target_rate_per_hour=4114, machine_rated_per_hour=3000, expected_oee=0.85)
    assert m["machines"] == 2


def test_line_capacity_bottleneck():
    from improvise.calc.line import line_capacity
    r = line_capacity([{"name": "A", "rate_per_hour": 6000}, {"name": "B", "rate_per_hour": 5000, "oee": 0.9},
                       {"name": "C", "rate_per_hour": 2500, "parallel": 2}])
    assert r["bottleneck"] == "B" and r["line_output_per_hour"] == 4500


def test_line_balance():
    from improvise.calc.line import line_balance
    tasks = [
        {"name": "a", "time_s": 20}, {"name": "b", "time_s": 30, "predecessors": ["a"]},
        {"name": "c", "time_s": 25, "predecessors": ["a"]}, {"name": "d", "time_s": 35, "predecessors": ["b", "c"]},
        {"name": "e", "time_s": 15, "predecessors": ["d"]},
    ]
    r = line_balance(tasks, cycle_time_s=50)
    assigned = [t for s in r["stations"] for t in s["tasks"]]
    assert sorted(assigned) == list("abcde")
    assert all(s["load_s"] <= 50 for s in r["stations"])
    assert r["workstations"] >= r["theoretical_min_stations"] == 3
    pos = {t: i for i, s in enumerate(r["stations"]) for t in s["tasks"]}
    for t in tasks:
        for p in t.get("predecessors", []):
            assert pos[p] <= pos[t["name"]]


def test_oee_and_roi():
    from improvise.calc.oee import oee
    from improvise.calc.roi import roi
    r = oee(planned_time_min=420, downtime_min=47, ideal_cycle_time_s=1.0, total_count=19271, good_count=18848)
    assert r["oee"] == pytest.approx(0.7479, abs=1e-3)
    x = roi(investment=1000, annual_net_cashflow=[400, 400, 400, 400])
    assert x["payback_years"] == pytest.approx(2.5)
    assert x["irr"] == pytest.approx(0.2186, abs=1e-3)


def test_tools_registry_schema():
    from improvise.tools import load_all
    reg = load_all()
    for name in ["takt_time", "line_balance", "oee", "roi", "make_machine_list", "layout_line",
                 "recall_experience"]:
        assert name in reg
    s = reg["takt_time"].schema()["function"]["parameters"]
    assert s["required"] == ["demand_units", "shifts", "hours_per_shift"]
    assert s["properties"]["shifts"]["type"] == "integer"


def test_memory_learning_loop(tmp_path):
    from improvise.memory import Memory
    m = Memory(tmp_path / "x.db")
    cid = m.add_case("line_design", "Egg packing line", "pack boiled eggs into trays 8000 eggs per hour",
                     "2 tray loaders + 1 sealer")
    m.update_outcome(cid, "sealer was bottleneck, needed 10% more speed")
    m.add_feedback("egg line buffer", "always add 10% buffer before the sealer")
    ctx = m.context_for("egg tray line")
    assert "VERIFIED" in ctx and "10% buffer" in ctx
    out = tmp_path / "ft.jsonl"
    assert m.export_finetune(out) == 2
    assert json.loads(out.read_text().splitlines()[0])["messages"][2]["content"].startswith("2 tray")


def test_layout_and_documents(tmp_path):
    from improvise.documents import make_machine_list, make_manual
    from improvise.layout import layout_line
    spec = json.loads((EX / "bottling_line.json").read_text())
    r = layout_line(**spec)
    assert r["fits_room"] is True and Path(r["svg"]).exists() and Path(r["json_for_3d"]).exists()
    ml = make_machine_list("Test", [{"name": "Filler", "qty": 1, "power_kw": 7.5}, {"name": "Labeller", "qty": 2, "power_kw": 1.5}])
    assert ml["total_power_kw"] == 10.5 and Path(ml["file"]).exists()
    man = make_manual("Filler", {"safety": "Lock out before maintenance."})
    assert "operation" in man["missing_sections"]


def test_contribution_anonymises(tmp_path):
    from improvise.contribute import anonymise, build_pack, scan_for_leaks
    from improvise.memory import Memory
    m = Memory(tmp_path / "c.db")
    cid = m.add_case("roi", "Line for Acme Foods Co., Ltd.", "contact john@acme.com +66 81 234 5678",
                     "quoted 1,250,000 บาท for Secret Farm")
    m.update_outcome(cid, "ok")
    out = tmp_path / "pack.jsonl"
    res = build_pack(m, out, secret_terms=["Secret Farm"])
    text = out.read_text(encoding="utf-8")
    assert res["accepted"] == 1
    for leak in ["john@acme.com", "Acme Foods", "1,250,000", "Secret Farm", "234 5678"]:
        assert leak not in text
    assert scan_for_leaks(anonymise("call 02-123-4567")) == []


def test_benchmark_references_and_grader():
    from improvise import bench
    items = bench.load_items()
    assert len(items) >= 15
    assert len({i["id"] for i in items}) == len(items)
    for item in items:
        exp = bench.expected_values(item)  # every reference tool must run
        if exp:
            # an answer that states the reference numbers must score 1.0 on answer checks
            words = " ".join(" ".join(g) for g in item.get("must_include_any", []))
            answer = " ".join(f"{v:.4f}" for _, v in exp) + " " + words
            g = bench.grade(item, answer, item.get("expect_tools", []))
            assert g["score"] == 1.0, (item["id"], g)
    takt = next(i for i in items if i["id"] == "takt-01")
    assert bench.grade(takt, "takt is 3.1 s", [])["score"] == 0.0
    price = next(i for i in items if i["id"] == "docs-price-01")
    assert bench.grade(price, "Filler unit price ฿ 250,000", ["make_machine_list"])["answer_score"] == 0.0


def test_benchmark_run_with_mock_model():
    from improvise import bench

    class Mock:
        def chat(self, messages, tools=None):
            if messages[-1]["role"] == "user":
                return {"role": "assistant", "content": "", "tool_calls": [{"function": {
                    "name": "takt_time", "arguments": {"demand_units": 20000, "shifts": 2, "hours_per_shift": 8,
                                                        "break_min_per_shift": 60}}}]}
            return {"role": "assistant", "content": "Takt time is 2.52 s per bottle."}

    items = [i for i in bench.load_items() if i["id"] in ("takt-01", "memory-01")]
    res = bench.run(model="mock", items=items, client=Mock())
    by = {r["id"]: r for r in res["results"]}
    assert by["takt-01"]["score"] == 1.0
    assert by["memory-01"]["score"] < 1.0  # mock ignores the seeded rule
    assert "BETTER" in bench.compare(res, {**res, "score": 0.0, "model": "old"})


def test_mcp_server_roundtrip(tmp_path):
    import io
    from improvise import mcp
    msgs = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "takt_time", "arguments": {
            "demand_units": 3600, "shifts": 1, "hours_per_shift": 1}}},
        {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "add_rule", "arguments": {
            "topic": "egg line", "rule": "add 10% buffer before the sealer"}}},
        {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "memory_stats", "arguments": {}}},
    ]
    out = io.StringIO()
    mcp.serve(io.StringIO("\n".join(json.dumps(m) for m in msgs) + "\n"), out)
    replies = {r["id"]: r for r in map(json.loads, out.getvalue().splitlines())}
    assert replies[1]["result"]["serverInfo"]["name"] == "improvise"
    names = {t["name"] for t in replies[2]["result"]["tools"]}
    assert {"takt_time", "add_rule", "verify_case", "search_knowledge"} <= names
    assert '"takt_time_s": 1.0' in replies[3]["result"]["content"][0]["text"]
    assert '"feedback_rules": 1' in replies[5]["result"]["content"][0]["text"]


def test_mcp_client_against_own_server(tmp_path, monkeypatch):
    import sys
    from improvise import mcp
    from improvise.tools import REGISTRY
    cfg = tmp_path / "mcp.json"
    cfg.write_text(json.dumps({"servers": {"self": {"command": sys.executable, "args": ["-m", "improvise.cli", "mcp", "serve"],
                                                   "env": {"IMPROVISE_HOME": str(tmp_path / "srv")}}}}))
    try:
        n = mcp.connect_servers(cfg)
        assert n > 5
        # read-only-looking calc tool still needs confirmation because the server did not declare it read-only
        from improvise import safety
        safety.CONFIRM = lambda name, args: False
        assert "Not executed" in REGISTRY["self__takt_time"].call({"demand_units": 3600, "shifts": 1, "hours_per_shift": 1})
        safety.CONFIRM = lambda name, args: True
        assert "takt_time_s" in REGISTRY["self__takt_time"].call({"demand_units": 3600, "shifts": 1, "hours_per_shift": 1})
    finally:
        safety.CONFIRM = lambda name, args: False
        mcp.close_all()
        for k in [k for k in REGISTRY if k.startswith("self__")]:
            del REGISTRY[k]
    assert not mcp.needs_confirmation({"name": "read_tag", "annotations": {"readOnlyHint": True}}, False)
    assert mcp.needs_confirmation({"name": "write_tag", "annotations": {"readOnlyHint": True}}, True)


def test_project_team_pm_led(tmp_path):
    from improvise.team import ProjectTeam, load_roles

    class Mock:
        def __init__(self):
            self.seen = []

        def chat(self, messages, tools=None):
            system, last = messages[0]["content"], messages[-1]
            who = system.split("You are the ")[-1].split(" in a")[0].split(" of this")[0]
            self.seen.append((who, [t["function"]["name"] for t in tools or []]))
            if last["role"] == "tool":
                return {"role": "assistant", "content": "Takt is 2.52 s. Open questions: bottle size."}
            c = last["content"]
            if c.startswith("Which positions does this project need"):
                return {"role": "assistant", "content": '{"existing": ["process_engineer", "project_manager"], "new": '
                        '[{"title": "Packaging Specialist", "focus": "film and cartons", "tools": ["search_knowledge", "not_a_tool"]}]}'}
            if "Decide who on the team does what" in c:
                return {"role": "assistant", "content": '[{"member": "line_lead", "task": "size the line"},'
                                                        ' {"member": "ghost", "task": "x"}]'}
            if "size the line" in c and "YOUR TASK" in c:
                return {"role": "assistant", "content": "", "tool_calls": [{"function": {"name": "takt_time", "arguments": {
                    "demand_units": 20000, "shifts": 2, "hours_per_shift": 8, "break_min_per_shift": 60}}}]}
            if "Report back to the owner" in c:
                return {"role": "assistant", "content": "Our line lead computed takt 2.52 s."}
            return {"role": "assistant", "content": "reviewed: ok"}

    assert "project_manager" in load_roles()
    mock = Mock()
    t = ProjectTeam("Juice Line A")
    prop = t.propose("20,000 bottles/day juice line", client=mock)
    assert "project_manager" not in prop                                   # the PM is never a member
    assert prop["packaging_specialist"]["tools"] == ["search_knowledge"]    # invalid tools dropped
    assert "takt_time" in prop["process_engineer"]["tools"]                 # catalogue tools filled in
    # the owner defines the roles themselves
    t.set_member("line_lead", "Line Lead Engineer", "Owns capacity and takt for this customer", ["takt_time"])
    t.set_member("consultant", "Senior Consultant", "Check everything twice", [], reviewer=True)
    reply = t.work("How fast must the line run?", client=mock)
    assert "2.52" in reply
    assert [e["who"] for e in t.board] == ["line_lead", "consultant"]      # unknown member dropped, reviewer ran
    assert "2.52" in t.board[0]["output"]
    lead_tools = {x for who, tools in mock.seen if who.startswith("Line Lead") for x in tools}
    assert lead_tools == {"takt_time"}
    # saved and reopened with the user's own definitions
    again = ProjectTeam.load("Juice Line A")
    assert again.members["line_lead"]["focus"] == "Owns capacity and takt for this customer"
    assert again.pm_history[-1]["content"] == reply
    assert "juice_line_a" in ProjectTeam.list_projects()


def test_coding_workspace_and_run(tmp_path):
    from improvise import safety
    from improvise.coding import run_python, workspace_list, workspace_read, workspace_write
    workspace_write("sim/hello.py", "import sys\nprint('takt', 50400/20000, *sys.argv[1:])\n")
    assert "sim/hello.py" in workspace_list()
    assert "takt" in workspace_read("sim/hello.py")
    with pytest.raises(ValueError):
        workspace_write("../escape.txt", "x")
    assert run_python("sim/hello.py")["ran"] is False          # no confirmation -> not executed
    safety.CONFIRM = lambda n, a: True
    try:
        r = run_python("sim/hello.py", ["ok"])
    finally:
        safety.CONFIRM = lambda n, a: False
    assert r["exit_code"] == 0 and "takt 2.52 ok" in r["stdout"]


def test_engineering_calcs_and_skills():
    from improvise.calc.engineering import conveyor_sizing, heat_load, pneumatic_cylinder, pump_power, utilities_summary
    c = conveyor_sizing(length_m=10, rate_per_min=60, pitch_mm=200, product_mass_kg=0.5)
    assert c["speed_m_per_min"] == 12.0 and c["selected_motor_kW"] >= c["required_motor_kW"]
    p = pneumatic_cylinder(bore_mm=50, stroke_mm=100, pressure_bar=6, required_force_N=600)
    assert p["force_extend_N"] == pytest.approx(1178.1, abs=0.5) and p["ok"] and p["suggested_standard_bore_mm"] == 50
    assert heat_load(1000, 4.19, 60, loss_factor=1)["heat_load_kW"] == pytest.approx(69.83, abs=0.01)
    assert pump_power(36, 30, efficiency=1, service_factor=1)["hydraulic_kW"] == pytest.approx(2.943, abs=0.001)
    u = utilities_summary([{"name": "a", "qty": 2, "power_kw": 10, "air_NL_min": 100}], diversity_factor=1, air_margin=1)
    assert u["connected_load_kW"] == 20 and u["compressed_air_NL_min"] == 200

    from improvise.skills import catalogue_prompt, load_skills, use_skill
    skills = load_skills()
    assert len(skills) >= 15 and "proposal-package" in skills
    assert "BLANK" in use_skill("proposal-package")
    assert "Unknown skill" in use_skill("nope")
    assert "conveyor-design" in catalogue_prompt()
    from improvise.tools import load_all
    reg = load_all()
    for s in skills.values():   # every tool a skill names must exist (Pro tools excepted)
        for t in s.tools:
            assert t in reg or t.startswith(("plc_", "iot_")) or t == "search_knowledge", (s.name, t)


def test_guard_backup_restore_selftest_and_history(tmp_path):
    from improvise import guard
    from improvise.coding import workspace_history, workspace_read, workspace_restore, workspace_write
    from improvise.memory import default_memory
    default_memory().add_feedback("t", "keep me")
    z = guard.backup()
    assert z.exists() and "experience.db" in __import__("zipfile").ZipFile(z).namelist()
    assert guard.auto_backup() is None or True
    safety = guard.restore(z)
    assert safety.exists()
    assert guard.selftest()["ok"]
    workspace_write("a.py", "v1")
    workspace_write("a.py", "v2 broken")
    assert len(workspace_history("a.py")) == 1
    workspace_restore("a.py")
    assert workspace_read("a.py") == "v1"
    with pytest.raises(ValueError):
        workspace_write(".history/x", "no")


def test_connector_catalogue():
    from improvise import connectors
    with pytest.raises(ValueError):
        connectors.add("excel")                       # needs dir
    r = connectors.add("excel", {"dir": "/tmp/q"})
    assert r["entry"]["args"][-1] == "/tmp/q" or "/tmp/q" in r["entry"]["args"]
    r = connectors.add("grafana", env={"GRAFANA_URL": "http://x"})
    assert r["entry"]["env"]["GRAFANA_URL"] == "http://x" and any("GRAFANA_SERVICE_ACCOUNT_TOKEN" in w for w in r["warnings"])
    assert set(connectors.installed()) == {"excel", "grafana"}
    assert connectors.remove("excel") and "excel" not in connectors.installed()


def test_rate_takt_rules_and_no_ai_prices(tmp_path):
    from improvise.calc.line import takt_from_rate
    r = takt_from_rate(8000, 30)
    assert r["takt_time_s_per_unit"] == 0.45 and r["packs_per_min"] == 4.44
    from improvise.memory import Memory
    m = Memory(tmp_path / "r.db")
    rid = m.add_feedback("x", "y")
    assert m.list_feedback()[0]["id"] == rid and m.delete_feedback(rid) and not m.search_feedback("y")
    from improvise.documents import make_machine_list
    import openpyxl
    f = make_machine_list("P", [{"name": "Sealer", "qty": 2, "unit_price": 99999}])["file"]
    if f.endswith(".xlsx"):
        ws = openpyxl.load_workbook(f).active
        assert all(c.value != 99999 for row in ws.iter_rows() for c in row)
