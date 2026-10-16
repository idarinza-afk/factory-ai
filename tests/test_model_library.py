import json


def _lib(tmp_path):
    d = tmp_path / "lib"
    (d / "models" / "retort-4b").mkdir(parents=True)
    (d / "catalog.json").write_text(json.dumps({"models": [
        {"id": "gap-belt", "name": "Gap belt", "category": "conveyor", "footprint_mm": {"L": 1240, "W": 400, "H": 800}}]}))
    (d / "models" / "retort-4b" / "meta.json").write_text(json.dumps({
        "id": "retort-4b", "name": "Water spray retort", "category": "retort", "tags": ["autoclave"],
        "footprint_mm": {"L": 5090, "W": 3035, "H": 2644},
        "connections": [{"name": "Load door", "at": [-2545, 0, 1100], "dir": [-1, 0, 0]}],
        "clearances_mm": {"service": 1000}}))
    return d


def test_learn_search_and_layout(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPROVISE_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("IMPROVISE_MODEL_LIBRARY", raising=False)
    from improvise import model_library as ml
    from improvise.tools import REGISTRY, load_all
    load_all()
    r = ml.learn(_lib(tmp_path))
    assert r["models"] == 2
    art = (tmp_path / "home" / "knowledge" / "model_library" / "retort-4b.md").read_text()
    assert "infeed end (-X)" in art and "height 1100 mm" in art
    hits = REGISTRY["find_machine_model"].call({"query": "autoclave"})
    assert hits[0]["model_id"] == "retort-4b"
    lay = REGISTRY["layout_line"].call({"project": "t", "machines": [{"name": "Retort", "model_id": "retort-4b"},
                                                                     {"name": "Gap belt"}]})
    assert lay["machines"][0]["length_mm"] == 5090 and lay["machines"][1]["width_mm"] == 400


def test_layout_uses_library_sizes_over_guesses(tmp_path, monkeypatch):
    monkeypatch.setenv("IMPROVISE_HOME", str(tmp_path / "home"))
    monkeypatch.delenv("IMPROVISE_MODEL_LIBRARY", raising=False)
    from improvise import model_library as ml
    from improvise.tools import REGISTRY, load_all
    load_all()
    ml.learn(_lib(tmp_path))
    lay = REGISTRY["layout_line"].call({"project": "t", "machines": [
        {"name": "Gap", "model_id": "gap-belt", "length_mm": 2000, "width_mm": 160},
        {"name": "Water spray retort unit", "length_mm": 5000, "width_mm": 3000}]})
    assert lay["machines"][0]["length_mm"] == 1240
    notes = " ".join(lay["model_library_notes"])
    assert "replaced by the library value" in notes and "retort-4b" in notes
