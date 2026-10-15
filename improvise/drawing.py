"""CAD-ready layout drawings (DXF) in an A3 sheet with frame, equipment list and title block.

Takes the machines placed by layout_line (or any list with x/y/length/width in mm) and
writes a DXF that opens in AutoCAD, DraftSight, LibreCAD, FreeCAD, etc.:
  * A3 landscape frame, model drawn at a scale that fits
  * machines as rectangles with numbers, flow arrows
  * overall dimensions in metres (red)
  * equipment list on the right, title block at the bottom (company, title, DWG NO., REV, DATE, UNIT, SCALE)
Needs ezdxf:  pip install improvise[cad]
"""

from __future__ import annotations

import datetime as dt
import re

from .tools import tool

A3 = (420.0, 297.0)          # mm, landscape
SCALES = [10, 20, 25, 50, 75, 100, 125, 150, 200, 250, 300, 400, 500]


@tool
def layout_dxf(title: str, machines: list[dict], room_length_mm: float = 0, room_width_mm: float = 0,
               company: str = "", dwg_no: str = "", rev: str = "A") -> dict:
    """Write an A3 DXF layout drawing (frame, machine outlines, dimensions in m, equipment list, title block).

    Args:
        title: drawing title, e.g. "Egg tray line - layout"
        machines: list of {"name", "x_mm", "y_mm", "length_mm", "width_mm"} in flow order (use layout_line's "machines")
        room_length_mm: room length to draw (0 = none)
        room_width_mm: room width to draw (0 = none)
        company: company name for the title block
        dwg_no: drawing number
        rev: revision
    """
    try:
        import ezdxf
    except ImportError:
        return {"error": "DXF drawings need ezdxf: pip install ezdxf"}
    from .config import load
    if not machines:
        raise ValueError("machines is empty")
    ext_x = max(room_length_mm, max(m["x_mm"] + m["length_mm"] for m in machines))
    ext_y = max(room_width_mm, max(m["y_mm"] + m["width_mm"] for m in machines))
    draw_w, draw_h = A3[0] - 20 - 110, A3[1] - 20 - 45      # minus margins, list column, title block
    scale = next((s for s in SCALES if ext_x / s <= draw_w and ext_y / s <= draw_h), SCALES[-1])
    doc = ezdxf.new("R2010", setup=True)
    for name, color in (("FRAME", 7), ("MACHINE", 5), ("ROOM", 8), ("DIM", 1), ("TEXT", 7), ("FLOW", 3)):
        doc.layers.add(name, color=color)
    msp = doc.modelspace()
    k = 1.0 / scale  # model mm -> paper mm; everything is drawn on paper scale
    ox, oy = 15.0, 55.0

    def rect(x, y, w, h, layer):
        msp.add_lwpolyline([(x, y), (x + w, y), (x + w, y + h), (x, y + h)], close=True, dxfattribs={"layer": layer})

    def text(s, x, y, h=2.5, layer="TEXT", align="LEFT"):
        t = msp.add_text(s, height=h, dxfattribs={"layer": layer})
        t.set_placement((x, y), align=getattr(ezdxf.enums.TextEntityAlignment, align))

    rect(10, 10, A3[0] - 20, A3[1] - 20, "FRAME")
    if room_length_mm and room_width_mm:
        rect(ox, oy, room_length_mm * k, room_width_mm * k, "ROOM")
    centres = []
    for i, m in enumerate(machines, 1):
        x, y = ox + m["x_mm"] * k, oy + m["y_mm"] * k
        w, h = m["length_mm"] * k, m["width_mm"] * k
        rect(x, y, w, h, "MACHINE")
        text(str(i), x + w / 2, y + h / 2, 3, align="MIDDLE_CENTER")
        centres.append((x + w / 2, y + h / 2))
    for a, b in zip(centres, centres[1:]):
        msp.add_line(a, b, dxfattribs={"layer": "FLOW", "linetype": "DASHED"})
    # overall dimensions (metres) in red
    dim_y = oy - 6
    msp.add_line((ox, dim_y), (ox + ext_x * k, dim_y), dxfattribs={"layer": "DIM"})
    text(f"{ext_x / 1000:.2f} m", ox + ext_x * k / 2, dim_y - 4, 2.5, "DIM", "MIDDLE_CENTER")
    dim_x = ox + ext_x * k + 5
    msp.add_line((dim_x, oy), (dim_x, oy + ext_y * k), dxfattribs={"layer": "DIM"})
    text(f"{ext_y / 1000:.2f} m", dim_x + 2, oy + ext_y * k / 2, 2.5, "DIM")
    # equipment list (right)
    lx = A3[0] - 10 - 105
    rect(lx, 55, 105, A3[1] - 10 - 55, "FRAME")
    text("EQUIPMENT LIST", lx + 3, A3[1] - 18, 3.5)
    yy = A3[1] - 26
    for i, m in enumerate(machines, 1):
        text(f"{i:>2}. {m['name'][:30]}", lx + 3, yy, 2.5)
        text(f"{m['length_mm']:.0f}x{m['width_mm']:.0f}", lx + 80, yy, 2.2)
        yy -= 5
    # title block (bottom)
    rect(10, 10, A3[0] - 20, 40, "FRAME")
    cells = [("COMPANY", company or "-"), ("TITLE", title), ("DWG NO.", dwg_no or "-"), ("REV", rev),
             ("DATE", dt.date.today().isoformat()), ("UNIT", "mm (dims in m)"), ("SCALE", f"1:{scale}")]
    widths = [70, 120, 50, 20, 40, 50, 50]
    x = 10.0
    for (lab, val), w in zip(cells, widths):
        msp.add_line((x, 10), (x, 50), dxfattribs={"layer": "FRAME"})
        text(lab, x + 2, 43, 2.2)
        text(str(val)[: int(w / 2.3)], x + 2, 28, 3.0)
        x += w
    out = load().output_dir / (re.sub(r"[^\w\-]+", "_", title).strip("_") + "_A3.dxf")
    doc.saveas(out)
    return {"dxf": str(out), "scale": f"1:{scale}", "sheet": "A3 landscape",
            "note": "Open in any CAD program; check dimensions and add the company logo block in CAD."}


@tool
def convert_units(value: float, from_unit: str, to_unit: str) -> dict:
    """Convert common engineering units (length, mass, pressure, power, flow, temperature, torque, speed).

    Args:
        value: the number to convert
        from_unit: e.g. mm, in, ft, kg, lb, bar, psi, kPa, kW, hp, m3/h, L/min, gpm, C, F, Nm, lbft, m/min, ft/min
        to_unit: target unit
    """
    f = {  # factor to SI base of each group
        "mm": ("L", 1e-3), "cm": ("L", 1e-2), "m": ("L", 1), "in": ("L", 0.0254), "ft": ("L", 0.3048),
        "g": ("M", 1e-3), "kg": ("M", 1), "t": ("M", 1000), "lb": ("M", 0.45359237),
        "pa": ("P", 1), "kpa": ("P", 1e3), "mpa": ("P", 1e6), "bar": ("P", 1e5), "psi": ("P", 6894.757), "mmhg": ("P", 133.322),
        "w": ("W", 1), "kw": ("W", 1e3), "hp": ("W", 745.7), "ps": ("W", 735.5),
        "m3/h": ("Q", 1 / 3600), "l/min": ("Q", 1 / 60000), "l/s": ("Q", 1e-3), "gpm": ("Q", 3.785411784e-3 / 60),
        "nm": ("T", 1), "kgfm": ("T", 9.80665), "lbft": ("T", 1.3558179),
        "m/s": ("V", 1), "m/min": ("V", 1 / 60), "ft/min": ("V", 0.3048 / 60), "km/h": ("V", 1 / 3.6),
        "kj": ("E", 1e3), "kwh": ("E", 3.6e6), "kcal": ("E", 4184), "btu": ("E", 1055.06),
    }
    a, b = from_unit.strip().lower(), to_unit.strip().lower()
    temps = {"c", "f", "k"}
    if a in temps and b in temps:
        c = value if a == "c" else (value - 32) * 5 / 9 if a == "f" else value - 273.15
        out = c if b == "c" else c * 9 / 5 + 32 if b == "f" else c + 273.15
        return {"value": round(out, 4), "unit": to_unit}
    if a not in f or b not in f:
        raise ValueError(f"unknown unit; known: {sorted(f) + sorted(temps)}")
    if f[a][0] != f[b][0]:
        raise ValueError(f"cannot convert {from_unit} to {to_unit} (different quantities)")
    return {"value": round(value * f[a][1] / f[b][1], 6), "unit": to_unit}
