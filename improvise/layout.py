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
    lib = os.environ.get("IMPROVISE_MODEL_LIBRARY")
    if not lib:
        return {}
    f = Path(lib) / "catalog.json"
    if not f.exists():
        return {}
    data = json.loads(f.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else data.get("models", data.get("items", []))
    return {str(i.get("name", "")).lower(): i for i in items if isinstance(i, dict)}


@tool
def layout_line(project: str, machines: list[dict], gap_mm: float = 1000, aisle_mm: float = 1500,
                room_length_mm: float = 0, room_width_mm: float = 0, rows: int = 1) -> dict:
    """Place machines in flow order (straight or U/serpentine with rows>1) and export SVG + JSON.

    Args:
        project: project name (used for file names)
        machines: list of {"name": str, "length_mm": float, "width_mm": float} in flow order
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
            hit = catalog.get(m["name"].lower())
            if hit:
                item["model_ref"] = hit.get("file") or hit.get("path") or hit.get("id")
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
            "fits_room": fits, "svg": str(svg_path), "json_for_3d": str(json_path), "machines": placed}
