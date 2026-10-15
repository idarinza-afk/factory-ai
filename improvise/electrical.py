"""Electrical diagrams for a machine or line (concept level, IEC-style symbols in SVG).

Sheet 1 - power: supply, main isolator, per motor protection (MPCB) + contactor (DOL) or
          MCB + VFD, motors with kW, the 24 VDC supply and the safety relay.
Sheet 2 - control: 24 VDC distribution, E-stop chain to the safety relay, PLC digital inputs
          and outputs with their field devices.
Plus a cable / component list (CSV). A concept for proposals and panel builders: the final
design (cable sizes, breaking capacity, selectivity, safety category) is done and signed by a
qualified electrical engineer to the local code.
"""

from __future__ import annotations

import csv
import html
import math
import re

from .tools import tool

W, H = 1189, 841  # A0-ish canvas units, scaled by the viewer


def _svg(title: str, body: list[str], sheet: str) -> str:
    tb = (f'<rect x="20" y="20" width="{W - 40}" height="{H - 40}" fill="none" stroke="#000" stroke-width="2"/>'
          f'<rect x="20" y="{H - 90}" width="{W - 40}" height="70" fill="none" stroke="#000"/>'
          f'<text x="40" y="{H - 50}" font-size="22" font-weight="bold">{html.escape(title)}</text>'
          f'<text x="40" y="{H - 28}" font-size="14">{html.escape(sheet)} - concept, to be completed and signed by a qualified electrical engineer</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Arial" font-size="13">'
            f'<rect width="{W}" height="{H}" fill="#fff"/>{tb}{"".join(body)}</svg>')


def _t(x, y, s, size=13, anchor="start", bold=False):
    weight = ' font-weight="bold"' if bold else ""
    return f'<text x="{x}" y="{y}" font-size="{size}" text-anchor="{anchor}"{weight}>{html.escape(str(s))}</text>'


def _l(x1, y1, x2, y2, w=1.5, dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-width="{w}"{d}/>'


def _box(x, y, w, h, label, sub=""):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#fff" stroke="#000" stroke-width="1.5"/>'
            + _t(x + w / 2, y + h / 2 - (2 if sub else -4), label, 13, "middle", True)
            + (_t(x + w / 2, y + h / 2 + 14, sub, 11, "middle") if sub else ""))


def _motor(cx, cy, tag, kw):
    return (f'<circle cx="{cx}" cy="{cy}" r="28" fill="#fff" stroke="#000" stroke-width="1.5"/>'
            + _t(cx, cy - 2, "M", 16, "middle", True) + _t(cx, cy + 14, "3~", 11, "middle")
            + _t(cx, cy + 48, tag, 13, "middle", True) + _t(cx, cy + 64, f"{kw} kW", 12, "middle"))


@tool
def electrical_schematic(title: str, motors: list[dict], inputs: list[dict] | None = None,
                         outputs: list[dict] | None = None, supply: str = "400 V 3~ 50 Hz + PE",
                         control_voltage: str = "24 VDC") -> dict:
    """Draw concept electrical diagrams (power + control/PLC I/O) as SVG/HTML and a component list CSV.

    Args:
        title: machine / line name
        motors: list of {"tag": "M1", "name": "Infeed conveyor", "kw": 0.37, "starter": "dol" or "vfd"}
        inputs: PLC digital inputs, list of {"tag": "B1", "name": "Transfer photo-eye", "address": "I0.0" (opt)}
        outputs: PLC digital outputs, list of {"tag": "K1", "name": "M1 run", "address": "Q0.0" (opt)}
        supply: mains supply text
        control_voltage: control voltage
    """
    from .config import load
    inputs, outputs = inputs or [], outputs or []
    if not motors:
        raise ValueError("motors is empty")
    comps: list[list] = [["Q0", "Main isolator / switch-disconnector", supply, "1"]]

    # ---------------- sheet 1: power
    b = [_t(40, 50, "POWER CIRCUIT", 18, bold=True), _t(40, 72, supply, 14)]
    y_bus = [110, 125, 140]
    x0, x_end = 140, W - 60
    for i, y in enumerate(y_bus):
        b.append(_l(x0, y, x_end, y, 2))
        b.append(_t(x0 - 30, y + 4, f"L{i + 1}", 12))
    b.append(_l(x0, 155, x_end, 155, 1, "6 3"))
    b.append(_t(x0 - 30, 159, "PE", 12))
    b.append(_box(40, 95, 60, 60, "Q0", "isolator"))
    n = len(motors) + 1
    step = (x_end - x0) / n
    for i, m in enumerate(motors):
        cx = x0 + step * (i + 0.5)
        tag = m.get("tag", f"M{i + 1}")
        starter = m.get("starter", "dol").lower()
        for y in y_bus:
            b.append(_l(cx - 10 + (y - 110) / 1.5, y, cx - 10 + (y - 110) / 1.5, 190))
        q = f"Q{i + 1}"
        if starter == "vfd":
            b.append(_box(cx - 40, 190, 80, 50, q, "MCB 3P"))
            b.append(_l(cx, 240, cx, 280))
            b.append(_box(cx - 45, 280, 90, 70, f"U{i + 1}", "VFD"))
            b.append(_l(cx, 350, cx, 420))
            comps += [[q, f"MCB 3-pole for VFD {tag}", "rated per VFD manual", "1"],
                      [f"U{i + 1}", f"Frequency inverter for {tag}", f"{m.get('kw', '')} kW, STO input", "1"]]
        else:
            b.append(_box(cx - 40, 190, 80, 50, q, "MPCB"))
            b.append(_l(cx, 240, cx, 280))
            b.append(_box(cx - 40, 280, 80, 50, f"K{i + 1}", "contactor"))
            b.append(_l(cx, 330, cx, 420))
            comps += [[q, f"Motor protection circuit breaker for {tag}", f"set to motor FLC ({m.get('kw', '')} kW)", "1"],
                      [f"K{i + 1}", f"Contactor for {tag}", f"AC-3, {control_voltage} coil", "1"]]
        b.append(_motor(cx, 450, tag, m.get("kw", "?")))
        b.append(_t(cx, 540, m.get("name", "")[:22], 12, "middle"))
        b.append(_l(cx + 28, 450, cx + 45, 450, 1, "6 3"))
        comps.append([tag, m.get("name", "motor"), f"{m.get('kw', '')} kW, IE3, IP55+", "1"])
    # PSU branch
    cx = x0 + step * (n - 0.5)
    b.append(_l(cx - 10, 110, cx - 10, 190))
    b.append(_box(cx - 40, 190, 80, 50, f"Q{n}", "MCB 1P+N"))
    b.append(_l(cx, 240, cx, 280))
    b.append(_box(cx - 50, 280, 100, 60, "G1", f"PSU {control_voltage}"))
    comps += [[f"Q{n}", "MCB for control power supply", "1P+N", "1"],
              ["G1", "Power supply", f"{control_voltage}, size for PLC + I/O + 30 %", "1"]]
    sheet1 = _svg(title, b, "Sheet 1 of 2 - power")

    # ---------------- sheet 2: control / PLC I/O
    c = [_t(40, 50, "CONTROL CIRCUIT AND PLC I/O", 18, bold=True), _t(40, 72, control_voltage, 14)]
    c.append(_l(80, 100, W - 60, 100, 2)); c.append(_t(40, 104, "+24V", 12))
    c.append(_l(80, H - 120, W - 60, H - 120, 2)); c.append(_t(40, H - 116, "0V", 12))
    # safety chain
    sx = W - 230
    c.append(_box(sx, 130, 130, 50, "S0", "E-STOP (2-ch)"))
    c.append(_box(sx, 220, 130, 60, "K0", "Safety relay"))
    c.append(_t(sx, 300, "K0 safe outputs drop:", 11))
    c.append(_t(sx, 316, "contactor coils / VFD STO", 11))
    c.append(_l(sx + 65, 100, sx + 65, 130)); c.append(_l(sx + 65, 180, sx + 65, 220))
    comps += [["S0", "Emergency stop push button", "2 NC contacts, mushroom head", "1"],
              ["K0", "Safety relay", "dual channel, PL per risk assessment", "1"],
              ["A1", "PLC CPU + digital I/O", f"{len(inputs)} DI / {len(outputs)} DO used + 20 % spare", "1"]]
    # PLC
    px, py, pw = 470, 140, 200
    rows = max(len(inputs), len(outputs), 1)
    ph = 40 + rows * 34
    c.append(f'<rect x="{px}" y="{py}" width="{pw}" height="{ph}" fill="#f4f6f8" stroke="#000" stroke-width="1.5"/>')
    c.append(_t(px + pw / 2, py + 22, "A1  PLC", 15, "middle", True))
    for i, s in enumerate(inputs):
        y = py + 50 + i * 34
        addr = s.get("address", f"I{i // 8}.{i % 8}")
        c.append(_t(px + 8, y + 4, addr, 12))
        c.append(_l(px, y, px - 120, y))
        c.append(_box(px - 230, y - 14, 110, 28, s.get("tag", f"B{i + 1}")))
        c.append(_t(px - 240, y + 4, s.get("name", "")[:28], 11, "end"))
        c.append(_l(px - 175, y - 14, px - 175, 100, 0.8, "3 3"))
        comps.append([s.get("tag", f"B{i + 1}"), s.get("name", "input"), "24 VDC PNP", "1"])
    for i, s in enumerate(outputs):
        y = py + 50 + i * 34
        addr = s.get("address", f"Q{i // 8}.{i % 8}")
        c.append(_t(px + pw - 8, y + 4, addr, 12, "end"))
        c.append(_l(px + pw, y, px + pw + 70, y))
        c.append(_box(px + pw + 70, y - 14, 100, 28, s.get("tag", f"K{i + 1}")))
        c.append(_t(px + pw + 180, y + 4, s.get("name", "")[:24], 11))
        c.append(_l(px + pw + 120, y + 14, px + pw + 120, H - 120, 0.8, "3 3"))
    c.append(_l(px + pw / 2, 100, px + pw / 2, py))
    c.append(_l(px + pw / 2, py + ph, px + pw / 2, H - 120))
    sheet2 = _svg(title, c, "Sheet 2 of 2 - control / PLC I/O")

    out = load().output_dir
    stem = re.sub(r"[^\w\-]+", "_", title).strip("_") or "electrical"
    p1, p2 = out / f"{stem}_electrical_1_power.svg", out / f"{stem}_electrical_2_control.svg"
    p1.write_text(sheet1, encoding="utf-8")
    p2.write_text(sheet2, encoding="utf-8")
    htm = out / f"{stem}_electrical.html"
    htm.write_text(f"<!doctype html><meta charset='utf-8'><title>{html.escape(title)} electrical</title>"
                   f"<body style='margin:0;background:#ddd'>{sheet1}<br>{sheet2}</body>", encoding="utf-8")
    csv_path = out / f"{stem}_electrical_components.csv"
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["Tag", "Description", "Rating / notes", "Qty"])
        w.writerows(comps)
    total_kw = sum(float(m.get("kw", 0) or 0) for m in motors)
    return {"power_svg": str(p1), "control_svg": str(p2), "viewer_html": str(htm), "components_csv": str(csv_path),
            "connected_motor_load_kW": round(total_kw, 2), "components": len(comps),
            "note": "Concept only: cable sizing, breaking capacity, safety category and code compliance by a qualified electrical engineer."}
