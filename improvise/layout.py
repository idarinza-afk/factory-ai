"""Line layout: place machines along a flow, check the room, export SVG + JSON for 3D.

The JSON export is CAD-neutral (positions in mm, footprint, rotation) so a 3D
tool (Blender, FreeCAD, your own model library...) can place real models.
Point IMPROVISE_MODEL_LIBRARY to a folder with catalog.json to match machine
names against your own 3D model library.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from .tools import tool


def _catalog() -> dict[str, dict]:
    """Model library entries by lower-case name and id (see improvise.model_library)."""
    from .model_library import load_library
    out: dict[str, dict] = {}
    for m in load_library():
        out[str(m.get("name", "")).lower()] = m
        out[m["id"].lower()] = m
    return out


@tool
def layout_line(project: str, machines: list[dict], gap_mm: float = 1000, aisle_mm: float = 1500,
                room_length_mm: float = 0, room_width_mm: float = 0, rows: int = 1) -> dict:
    """Place machines in flow order (straight or U/serpentine with rows>1) and export SVG + JSON.

    Args:
        project: project name (used for file names)
        machines: list of {"name": str, "length_mm": float, "width_mm": float} in flow order. With a model library
            connected, give {"name", "model_id"} and the real footprint is used.
        gap_mm: clearance between machines along the flow
        aisle_mm: operator/maintenance aisle around and between rows
        room_length_mm: room length to check against (0 = no check)
        room_width_mm: room width to check against (0 = no check)
        rows: number of rows; >1 folds the line into a U / serpentine
    """
    from .config import load
    if not machines:
        raise ValueError("machines is empty")
    rows = max(1, int(rows))
    per_row = -(-len(machines) // rows)
    catalog = _catalog()
    resolved, lib_notes = [], []
    for m in machines:  # real footprints from the model library when a model is referenced
        m = dict(m)
        hit = catalog.get(str(m.get("model_id", "")).lower()) or catalog.get(str(m.get("name", "")).lower())
        if hit:
            fp = hit.get("footprint_mm") or {}
            for key, k in (("length_mm", "L"), ("width_mm", "W"), ("height_mm", "H")):
                if fp.get(k):
                    if m.get(key) and abs(float(m[key]) - float(fp[k])) > 0.05 * float(fp[k]):
                        lib_notes.append(f"{m.get('name')}: {key} {m[key]} replaced by the library value {fp[k]}")
                    m[key] = fp[k]
            m["_model"] = hit
        elif catalog:
            from .model_library import find_models
            cands = [c["id"] for c in find_models(str(m.get("name", "")), limit=2)]
            lib_notes.append(f"{m.get('name')}: not linked to the model library (sizes as given)"
                             + (f" - matching models: {', '.join(cands)}; pass model_id to use the real design" if cands else ""))
        if not m.get("length_mm") or not m.get("width_mm"):
            raise ValueError(f"{m.get('name')}: give length_mm and width_mm (or a model_id from find_machine_model)")
        resolved.append(m)
    machines = resolved
    row_lengths = []
    for r in range(rows):
        chunk = machines[r * per_row:(r + 1) * per_row]
        if chunk:
            row_lengths.append(sum(m["length_mm"] for m in chunk) + gap_mm * (len(chunk) - 1))
    longest = max(row_lengths)
    placed, y, max_len = [], aisle_mm, 0.0
    for r in range(rows):
        chunk = machines[r * per_row:(r + 1) * per_row]
        if not chunk:
            break
        if r % 2 == 1:
            chunk = list(reversed(chunk))
        row_w = max(m["width_mm"] for m in chunk)
        # return rows are right-aligned so the flow turns at the end of the previous row
        x = aisle_mm + (longest - row_lengths[r] if r % 2 == 1 else 0)
        for m in chunk:
            item = {
                "name": m["name"], "x_mm": x, "y_mm": y + (row_w - m["width_mm"]) / 2,
                "length_mm": m["length_mm"], "width_mm": m["width_mm"],
                "rotation_deg": 180 if r % 2 == 1 else 0, "row": r + 1,
            }
            if m.get("height_mm"):
                item["height_mm"] = m["height_mm"]
            hit = m.get("_model")
            if hit:
                item["model_id"] = hit["id"]
                if hit.get("clearances_mm"):
                    item["clearances_mm"] = hit["clearances_mm"]
            placed.append(item)
            x += m["length_mm"] + gap_mm
        max_len = max(max_len, x - gap_mm + aisle_mm)
        y += row_w + aisle_mm
    total_w = y
    order = {m["name"]: i for i, m in enumerate(machines)}
    placed.sort(key=lambda p: order.get(p["name"], 0))

    fits = None
    if room_length_mm and room_width_mm:
        fits = max_len <= room_length_mm and total_w <= room_width_mm

    out = load().output_dir
    stem = "".join(c if c.isalnum() or c in "-_" else "_" for c in project)
    svg_path = out / f"{stem}_layout.svg"
    json_path = out / f"{stem}_layout.json"
    W, H = max(max_len, room_length_mm or 0), max(total_w, room_width_mm or 0)
    s = 1000 / W
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W*s+40:.0f}" height="{H*s+60:.0f}" font-family="Arial" font-size="11">',
             '<g transform="translate(20,20)">']
    if room_length_mm and room_width_mm:
        parts.append(f'<rect x="0" y="0" width="{room_length_mm*s:.1f}" height="{room_width_mm*s:.1f}" fill="none" stroke="#888" stroke-dasharray="6 4"/>')
    for i, p in enumerate(placed, start=1):
        parts.append(f'<rect x="{p["x_mm"]*s:.1f}" y="{p["y_mm"]*s:.1f}" width="{p["length_mm"]*s:.1f}" height="{p["width_mm"]*s:.1f}" fill="#dbe8f5" stroke="#1f4e78"/>')
        parts.append(f'<text x="{(p["x_mm"]+p["length_mm"]/2)*s:.1f}" y="{(p["y_mm"]+p["width_mm"]/2)*s+4:.1f}" text-anchor="middle">{i}. {p["name"]}</text>')
    for a, b in zip(placed, placed[1:]):
        ax, ay = (a["x_mm"] + a["length_mm"] / 2) * s, (a["y_mm"] + a["width_mm"] / 2) * s
        bx, by = (b["x_mm"] + b["length_mm"] / 2) * s, (b["y_mm"] + b["width_mm"] / 2) * s
        parts.append(f'<line x1="{ax:.1f}" y1="{ay:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="#c62828" stroke-width="1.5" stroke-dasharray="4 3" opacity="0.6"/>')
    parts.append(f'<text x="0" y="{H*s+30:.0f}">Line envelope {max_len/1000:.2f} m x {total_w/1000:.2f} m (dims in m)</text>')
    parts.append("</g></svg>")
    svg_path.write_text("\n".join(parts), encoding="utf-8")
    json_path.write_text(json.dumps({"project": project, "units": "mm", "machines": placed}, indent=2), encoding="utf-8")
    return {"envelope_length_m": round(max_len / 1000, 2), "envelope_width_m": round(total_w / 1000, 2),
            "fits_room": fits, "svg": str(svg_path), "json_for_3d": str(json_path), "machines": placed,
            **({"model_library_notes": lib_notes} if lib_notes else {})}
