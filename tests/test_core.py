import json
from pathlib import Path

import pytest

EX = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture(autouse=True)
def _home(tmp_path, monkeypatch):
    monkeypatch.setenv("FACTORY_AI_HOME", str(tmp_path))
    import factory_ai.memory as mem
    import factory_ai.knowledge as kb
    mem._default = None
    kb._kb = None


def test_takt_and_machines():
    from factory_ai.calc.line import machines_required, takt_time
    t = takt_time(demand_units=57600, shifts=2, hours_per_shift=8, break_min_per_shift=60)
    assert t["available_time_s"] == 50400
    assert t["takt_time_s"] == pytest.approx(0.875)
    m = machines_required(target_rate_per_hour=4114, machine_rated_per_hour=3000, expected_oee=0.85)
    assert m["machines"] == 2


def test_line_capacity_bottleneck():
    from factory_ai.calc.line import line_capacity
    r = line_capacity([{"name": "A", "rate_per_hour": 6000}, {"name": "B", "rate_per_hour": 5000, "oee": 0.9},
                       {"name": "C", "rate_per_hour": 2500, "parallel": 2}])
    assert r["bottleneck"] == "B" and r["line_output_per_hour"] == 4500


def test_line_balance():
    from factory_ai.calc.line import line_balance
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
    from factory_ai.calc.oee import oee
    from factory_ai.calc.roi import roi
    r = oee(planned_time_min=420, downtime_min=47, ideal_cycle_time_s=1.0, total_count=19271, good_count=18848)
    assert r["oee"] == pytest.approx(0.7479, abs=1e-3)
    x = roi(investment=1000, annual_net_cashflow=[400, 400, 400, 400])
    assert x["payback_years"] == pytest.approx(2.5)
    assert x["irr"] == pytest.approx(0.2186, abs=1e-3)


def test_tools_registry_schema():
    from factory_ai.tools import load_all
    reg = load_all()
    for name in ["takt_time", "line_balance", "oee", "roi", "make_machine_list", "layout_line",
                 "recall_experience"]:
        assert name in reg
    s = reg["takt_time"].schema()["function"]["parameters"]
    assert s["required"] == ["demand_units", "shifts", "hours_per_shift"]
    assert s["properties"]["shifts"]["type"] == "integer"


def test_memory_learning_loop(tmp_path):
    from factory_ai.memory import Memory
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
    from factory_ai.documents import make_machine_list, make_manual
    from factory_ai.layout import layout_line
    spec = json.loads((EX / "bottling_line.json").read_text())
    r = layout_line(**spec)
    assert r["fits_room"] is True and Path(r["svg"]).exists() and Path(r["json_for_3d"]).exists()
    ml = make_machine_list("Test", [{"name": "Filler", "qty": 1, "power_kw": 7.5}, {"name": "Labeller", "qty": 2, "power_kw": 1.5}])
    assert ml["total_power_kw"] == 10.5 and Path(ml["file"]).exists()
    man = make_manual("Filler", {"safety": "Lock out before maintenance."})
    assert "operation" in man["missing_sections"]


def test_contribution_anonymises(tmp_path):
    from factory_ai.contribute import anonymise, build_pack, scan_for_leaks
    from factory_ai.memory import Memory
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
    from factory_ai import bench
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
    from factory_ai import bench

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
    from factory_ai import mcp
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
    assert replies[1]["result"]["serverInfo"]["name"] == "factory-ai"
    names = {t["name"] for t in replies[2]["result"]["tools"]}
    assert {"takt_time", "add_rule", "verify_case", "search_knowledge"} <= names
    assert '"takt_time_s": 1.0' in replies[3]["result"]["content"][0]["text"]
    assert '"feedback_rules": 1' in replies[5]["result"]["content"][0]["text"]


def test_mcp_client_against_own_server(tmp_path, monkeypatch):
    import sys
    from factory_ai import mcp
    from factory_ai.tools import REGISTRY
    cfg = tmp_path / "mcp.json"
    cfg.write_text(json.dumps({"servers": {"self": {"command": sys.executable, "args": ["-m", "factory_ai.cli", "mcp", "serve"],
                                                   "env": {"FACTORY_AI_HOME": str(tmp_path / "srv")}}}}))
    try:
        n = mcp.connect_servers(cfg)
        assert n > 5
        # read-only-looking calc tool still needs confirmation because the server did not declare it read-only
        mcp.CONFIRM = lambda name, args: False
        assert "Not executed" in REGISTRY["self__takt_time"].call({"demand_units": 3600, "shifts": 1, "hours_per_shift": 1})
        mcp.CONFIRM = lambda name, args: True
        assert "takt_time_s" in REGISTRY["self__takt_time"].call({"demand_units": 3600, "shifts": 1, "hours_per_shift": 1})
    finally:
        mcp.close_all()
        for k in [k for k in REGISTRY if k.startswith("self__")]:
            del REGISTRY[k]
    assert not mcp.needs_confirmation({"name": "read_tag", "annotations": {"readOnlyHint": True}}, False)
    assert mcp.needs_confirmation({"name": "write_tag", "annotations": {"readOnlyHint": True}}, True)
