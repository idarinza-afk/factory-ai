"""Your own 3D machine model library: let Improvise know every machine's design.

A library is a folder with catalog.json and models/<id>/meta.json (schema "diatonic-model/1":
footprint, envelope, specs, connection points, clearances, service side, sources...).
`improvise library learn <folder>` remembers the folder and writes one knowledge article per
machine into ~/.improvise/knowledge/model_library, so every answer can draw on the real
designs. The tools below let the assistant search the library and read a machine's details,
and layout_line takes real footprints from it. Everything stays on this computer.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from .tools import tool

POINTER = "model_library_path.txt"


def library_dir() -> Path | None:
    env = os.environ.get("IMPROVISE_MODEL_LIBRARY")
    if env:
        return Path(env)
    from .config import load
    p = load().home / POINTER
    if p.exists():
        d = Path(p.read_text(encoding="utf-8").strip())
        return d if d.exists() else None
    return None


_cache: tuple[str, float, list[dict]] | None = None


def load_library(folder: Path | None = None) -> list[dict]:
    """Every model: the catalog entry merged with its meta.json (meta wins)."""
    global _cache
    d = folder or library_dir()
    if not d or not d.exists():
        return []
    cat_file = d / "catalog.json"
    metas = sorted((d / "models").glob("*/meta.json")) if (d / "models").exists() else []
    stamp = max([cat_file.stat().st_mtime if cat_file.exists() else 0.0] + [f.stat().st_mtime for f in metas])
    if _cache and _cache[0] == str(d) and _cache[1] == stamp:
        return _cache[2]
    by_id: dict[str, dict] = {}
    if cat_file.exists():
        data = json.loads(cat_file.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("models", data.get("items", []))
        for it in items:
            if isinstance(it, dict) and it.get("id"):
                by_id[it["id"]] = dict(it)
    for meta in metas:
        try:
            m = json.loads(meta.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        mid = m.get("id") or meta.parent.name
        by_id[mid] = {**by_id.get(mid, {}), **m, "id": mid, "_dir": str(meta.parent)}
    for m in by_id.values():
        m["footprint_mm"] = _norm_footprint(m)
    models = sorted(by_id.values(), key=lambda m: (str(m.get("category", "")), m["id"]))
    _cache = (str(d), stamp, models)
    return models


def _norm_footprint(m: dict) -> dict:
    """Libraries write footprints as {L,W,H}, [L,W(,H)] or only an envelope: make it {L,W,H} (mm)."""
    f = m.get("footprint_mm")
    if isinstance(f, (list, tuple)):
        f = dict(zip("LWH", f))
    if isinstance(f, dict) and f.get("L") and f.get("W"):
        return {"L": f.get("L"), "W": f.get("W"), "H": f.get("H"), **{k: v for k, v in f.items() if k not in "LWH"}}
    env = m.get("envelope_mm")
    if isinstance(env, (list, tuple)) and len(env) >= 2:
        return dict(zip("LWH", env))
    if isinstance(env, dict):
        try:
            dims = [abs(float(env[a][1]) - float(env[a][0])) for a in ("x", "y", "z") if a in env]
            return dict(zip("LWH", [round(x) for x in dims]))
        except (TypeError, ValueError, IndexError, KeyError):
            pass
    return {"L": None, "W": None, "H": None}


def _words(s: str) -> set[str]:
    w = set(re.findall(r"[a-z0-9]+", s.lower().replace("-", " ")))
    return w | {x[:-1] for x in w if x.endswith("s") and len(x) > 3}


def _hay(m: dict) -> str:
    return " ".join(str(m.get(k, "")) for k in ("id", "name", "category", "line_role", "key_specs", "brand")) + " " + \
        " ".join(m.get("tags", []) or [])


def _footprint(m: dict) -> dict:
    f = _norm_footprint(m)
    return {"L": f.get("L"), "W": f.get("W"), "H": f.get("H")}


def find_models(query: str, category: str = "", limit: int = 8) -> list[dict]:
    q = _words(query)
    out = []
    for m in load_library():
        if category and category.lower() not in str(m.get("category", "")).lower():
            continue
        score = len(q & _words(_hay(m))) if q else 1
        if score:
            out.append((score, m))
    out.sort(key=lambda x: -x[0])
    return [m for _, m in out[:limit]]


def _side(vec) -> str:
    try:
        x, y, z = (float(v) for v in vec)
    except (TypeError, ValueError):
        return ""
    axis = max((abs(x), "X"), (abs(y), "Y"), (abs(z), "Z"))[1]
    val = {"X": x, "Y": y, "Z": z}[axis]
    return {"X": "outfeed end (+X)" if val > 0 else "infeed end (-X)",
            "Y": "service side (+Y)" if val > 0 else "far side (-Y)",
            "Z": "top (+Z)" if val > 0 else "underneath (-Z)"}[axis]


def article(m: dict) -> str:
    """One knowledge article about a machine design (most important facts first)."""
    f = _footprint(m)
    lines = [f"# {m.get('name', m['id'])}",
             f"Library model id: {m['id']} | category: {m.get('category', '')} | status: {m.get('status', '')}",
             f"Footprint L x W x H: {f['L']} x {f['W']} x {f['H']} mm (L along the product flow, X axis)."]
    pl = pass_line(m)
    if pl["infeed_mm"] or pl["outfeed_mm"]:
        lines.append(f"Pass line (product height): infeed {pl['infeed_mm']} mm, outfeed {pl['outfeed_mm']} mm.")
    if m.get("line_role"):
        lines.append(f"Role in the line: {m['line_role']}")
    if m.get("key_specs"):
        lines.append(f"Key specs: {m['key_specs']}")
    if m.get("tags"):
        lines.append("Also called: " + ", ".join(m["tags"]))
    specs = m.get("specs") or {}
    if specs:
        lines.append("Specifications:")
        lines += [f"- {k.replace('_', ' ')}: {v if not isinstance(v, list) else ' x '.join(map(str, v))}" for k, v in specs.items()]
    for k, label in (("main_axis", "Orientation"), ("service_side", "Service side"), ("origin", "Model origin")):
        if m.get(k):
            lines.append(f"{label}: {m[k]}")
    conns = m.get("connections") or []
    if conns:
        lines.append("Connection points (x, y, z in mm from the origin):")
        for c in conns:
            at = c.get("at")
            h = f", height {at[2]} mm" if isinstance(at, list) and len(at) == 3 else ""
            lines.append(f"- {c.get('name', '')}: {_side(c.get('dir'))} at {at}{h}")
    cl = m.get("clearances_mm") or {}
    if cl:
        lines.append("Clearances needed (mm): " + "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in cl.items()))
    if m.get("assumptions"):
        lines.append(f"Assumptions: {m['assumptions']}")
    if m.get("used_in"):
        lines.append("Used in: " + ", ".join(m["used_in"]))
    if m.get("sources"):
        lines.append("Sources: " + "; ".join(m["sources"]))
    lines.append("Files: 3D model (.step/.obj/.solidcraft) and preview image are in the model library folder.")
    return "\n".join(lines) + "\n"


def learn(folder: str | Path) -> dict:
    """Remember the library folder and (re)write one knowledge article per machine."""
    from .config import load
    d = Path(folder).expanduser().resolve()
    models = load_library(d)
    if not models:
        raise ValueError(f"no models found in {d} (expected catalog.json and models/<id>/meta.json)")
    cfg = load()
    cfg.ensure_dirs()
    (cfg.home / POINTER).write_text(str(d), encoding="utf-8")
    kdir = cfg.user_knowledge_dir / "model_library"
    kdir.mkdir(parents=True, exist_ok=True)
    for old in kdir.glob("*.md"):
        old.unlink()
    cats: dict[str, list[dict]] = {}
    for m in models:
        (kdir / f"{m['id']}.md").write_text(article(m), encoding="utf-8")
        cats.setdefault(m.get("category", "other"), []).append(m)
    overview = ["# Machine model library - overview", f"Folder: {d}. {len(models)} machine designs, by category:"]
    for c, ms in sorted(cats.items()):
        overview.append(f"## {c}")
        overview += [f"- {m['id']}: {m.get('name', '')} ({_footprint(m)['L']} x {_footprint(m)['W']} mm)" for m in ms]
    (kdir / "_overview.md").write_text("\n".join(overview) + "\n", encoding="utf-8")
    try:  # rebuild the search index so the new articles are used right away
        from . import knowledge
        knowledge._kb = None
    except Exception:
        pass
    return {"library": str(d), "models": len(models), "categories": len(cats), "knowledge_dir": str(kdir)}


def _conn_height(m: dict, side: str) -> float | None:
    """Product infeed (-X) or outfeed (+X) height from the connection points."""
    want = -1 if side == "in" else 1
    words = ("infeed", "load", "in ") if side == "in" else ("outfeed", "unload", "out ")
    best = None
    for c in m.get("connections") or []:
        at, d = c.get("at"), c.get("dir")
        name = str(c.get("name", "")).lower() + " "
        if not (isinstance(at, list) and len(at) == 3):
            continue
        if isinstance(d, list) and len(d) == 3 and d[0] == want and abs(d[1]) < 1e-9 and abs(d[2]) < 1e-9:
            if any(w in name for w in words) or best is None:
                best = float(at[2])
    return best


def pass_line(m: dict) -> dict:
    """Product transfer heights of a model: infeed, outfeed (mm) from connections, specs or key specs."""
    spec = (m.get("specs") or {}).get("pass_line_mm")
    txt = re.search(r"pass line\s*(\d{3,4})", str(m.get("key_specs", "")), re.I)
    base = float(spec) if isinstance(spec, (int, float)) else (float(txt.group(1)) if txt else None)
    return {"infeed_mm": _conn_height(m, "in") or base, "outfeed_mm": _conn_height(m, "out") or base,
            "nominal_mm": base}


def footprint_for(name_or_id: str) -> dict | None:
    """Exact id, exact name, or a single best search hit."""
    key = name_or_id.strip().lower()
    models = load_library()
    for m in models:
        if m["id"].lower() == key or str(m.get("name", "")).lower() == key:
            return m
    return None


@tool
def find_machine_model(query: str, category: str = "") -> list:
    """Search YOUR 3D machine model library (real designs with footprints, specs, connections, clearances).
    Use it before assuming machine sizes in a layout or a machine list.

    Args:
        query: what the machine does or is called, e.g. "retort 4 baskets", "checkweigher pouch", "gap belt"
        category: optional category filter, e.g. retort, conveyor, xray, checkweigher, packer
    """
    if not library_dir():
        return [{"message": "No model library connected. Run: improvise library learn <folder with catalog.json>"}]
    hits = find_models(query, category)
    if not hits:
        cats = sorted({m.get("category", "") for m in load_library()})
        return [{"message": "no match", "categories": cats}]
    return [{"model_id": m["id"], "name": m.get("name"), "category": m.get("category"), "footprint_mm": _footprint(m),
             "key_specs": m.get("key_specs", ""), "line_role": m.get("line_role", ""), "status": m.get("status", "")}
            for m in hits]


@tool
def machine_model_details(model_id: str) -> dict:
    """Full design details of one machine in YOUR model library: specs, envelope, connection points
    (infeed/outfeed heights, utilities), clearances, service side, sources and files.

    Args:
        model_id: id from find_machine_model
    """
    m = footprint_for(model_id)
    if not m:
        hits = find_models(model_id, limit=3)
        raise ValueError("unknown model_id" + (f"; did you mean: {', '.join(h['id'] for h in hits)}" if hits else ""))
    d = Path(m.get("_dir", ""))
    files = {k: str(d / v) for k, v in (m.get("files") or {}).items() if (d / v).exists()} if d else {}
    keep = ("id", "name", "brand", "category", "line_role", "tags", "key_specs", "footprint_mm", "envelope_mm", "specs",
            "main_axis", "service_side", "origin", "connections", "clearances_mm", "assumptions", "sources", "used_in",
            "status")
    return {**{k: m[k] for k in keep if k in m}, "files": files,
            "note": "Model sizes are as recorded in the library; check the status before using them for a final layout."}
