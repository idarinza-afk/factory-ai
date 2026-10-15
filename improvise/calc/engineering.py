"""Common machine-design calculations used by the skills.

All formulas are standard first-order engineering estimates; results are for
sizing and proposals and must be confirmed with supplier data.
"""

from __future__ import annotations

import math

from ..tools import tool

G = 9.81
IEC_MOTORS_KW = [0.09, 0.12, 0.18, 0.25, 0.37, 0.55, 0.75, 1.1, 1.5, 2.2, 3.0, 4.0, 5.5, 7.5, 11, 15, 18.5, 22,
                 30, 37, 45, 55, 75, 90, 110, 132, 160, 200, 250, 315]


def next_motor(kw: float) -> float:
    for m in IEC_MOTORS_KW:
        if m >= kw:
            return m
    return math.ceil(kw)


@tool
def conveyor_sizing(length_m: float, rate_per_min: float, pitch_mm: float, product_mass_kg: float,
                    belt_mass_kg_per_m: float = 3.0, friction: float = 0.3, incline_deg: float = 0,
                    efficiency: float = 0.8, service_factor: float = 1.5) -> dict:
    """Belt/chain conveyor: required speed, belt pull and motor power (next IEC size).

    Args:
        length_m: conveyor length between pulley centres in m
        rate_per_min: products per minute to transport
        pitch_mm: spacing between products on the belt in mm (product length + gap)
        product_mass_kg: mass of one product in kg
        belt_mass_kg_per_m: belt/chain mass per metre of conveyor length, default 3.0
        friction: belt-to-bed friction coefficient (slider bed ~0.3, rollers ~0.05), default 0.3
        incline_deg: incline angle in degrees, default 0
        efficiency: drive efficiency (gearbox etc.), default 0.8
        service_factor: margin on motor power, default 1.5
    """
    v = rate_per_min * pitch_mm / 1000 / 60  # m/s
    load = length_m / (pitch_mm / 1000) * product_mass_kg
    belt = 2 * length_m * belt_mass_kg_per_m
    th = math.radians(incline_deg)
    force = G * (friction * (load + belt) * math.cos(th) + load * math.sin(th))
    p_shaft = force * v / 1000
    p_motor = p_shaft / efficiency * service_factor
    return {"speed_m_per_min": round(v * 60, 2), "speed_m_per_s": round(v, 3), "load_on_belt_kg": round(load, 1),
            "effective_pull_N": round(force, 1), "shaft_power_kW": round(p_shaft, 3),
            "required_motor_kW": round(p_motor, 3), "selected_motor_kW": next_motor(p_motor)}


@tool
def pneumatic_cylinder(bore_mm: float, stroke_mm: float, pressure_bar: float = 6, rod_mm: float = 0,
                       cycles_per_min: float = 0, required_force_N: float = 0, load_factor: float = 0.7) -> dict:
    """Double-acting cylinder: theoretical/usable force and free-air consumption; checks a required force.

    Args:
        bore_mm: piston diameter in mm
        stroke_mm: stroke in mm
        pressure_bar: working gauge pressure in bar, default 6
        rod_mm: rod diameter in mm (0 = use 0.3 x bore)
        cycles_per_min: double strokes per minute for air consumption
        required_force_N: force the application needs (0 = no check)
        load_factor: usable share of theoretical force (dynamic ~0.5-0.7, static ~0.8), default 0.7
    """
    rod = rod_mm or 0.3 * bore_mm
    a_ext = math.pi * (bore_mm / 1000) ** 2 / 4
    a_ret = a_ext - math.pi * (rod / 1000) ** 2 / 4
    p = pressure_bar * 1e5
    f_ext, f_ret = p * a_ext, p * a_ret
    ratio = (pressure_bar + 1.013) / 1.013
    nl_per_cycle = (a_ext + a_ret) * stroke_mm / 1000 * ratio * 1000
    res = {"force_extend_N": round(f_ext, 1), "force_retract_N": round(f_ret, 1),
           "usable_extend_N": round(f_ext * load_factor, 1), "air_NL_per_cycle": round(nl_per_cycle, 3),
           "air_NL_per_min": round(nl_per_cycle * cycles_per_min, 2)}
    if required_force_N:
        min_bore = math.sqrt(4 * required_force_N / (load_factor * p * math.pi)) * 1000
        std = [8, 10, 12, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125, 160, 200, 250, 320]
        res.update({"ok": f_ext * load_factor >= required_force_N, "minimum_bore_mm": round(min_bore, 1),
                    "suggested_standard_bore_mm": next((b for b in std if b >= min_bore), None)})
    return res


@tool
def heat_load(mass_flow_kg_per_h: float, cp_kJ_per_kgK: float, delta_T_K: float, loss_factor: float = 1.15,
              latent_heat_kJ_per_kg: float = 2100) -> dict:
    """Heating duty Q = m x cp x dT (with losses) and the saturated steam needed to supply it.

    Args:
        mass_flow_kg_per_h: product or water flow in kg/h
        cp_kJ_per_kgK: specific heat (water ~4.19, most foods 3.0-3.9)
        delta_T_K: temperature rise in K
        loss_factor: allowance for losses, default 1.15
        latent_heat_kJ_per_kg: steam latent heat at supply pressure (~2100 at 4-6 barg), default 2100
    """
    q_kw = mass_flow_kg_per_h * cp_kJ_per_kgK * delta_T_K / 3600 * loss_factor
    return {"heat_load_kW": round(q_kw, 2), "steam_kg_per_h": round(q_kw * 3600 / latent_heat_kJ_per_kg, 1)}


@tool
def pump_power(flow_m3_per_h: float, head_m: float, density_kg_m3: float = 1000, efficiency: float = 0.6,
               service_factor: float = 1.15) -> dict:
    """Hydraulic and motor power of a pump (next IEC motor size).

    Args:
        flow_m3_per_h: flow in m3/h
        head_m: total dynamic head in m
        density_kg_m3: fluid density, default 1000
        efficiency: pump efficiency, default 0.6
        service_factor: motor margin, default 1.15
    """
    p_h = density_kg_m3 * G * flow_m3_per_h / 3600 * head_m / 1000
    p_m = p_h / efficiency * service_factor
    return {"hydraulic_kW": round(p_h, 3), "required_motor_kW": round(p_m, 3), "selected_motor_kW": next_motor(p_m)}


@tool
def utilities_summary(machines: list[dict], diversity_factor: float = 0.8, power_factor: float = 0.85,
                      air_margin: float = 1.3) -> dict:
    """Total utilities of a line: power (kW and transformer kVA), compressed air, water, steam.

    Args:
        machines: list of {"name", "qty" (opt), "power_kw", "air_NL_min" (opt), "water_L_h" (opt), "steam_kg_h" (opt)}
        diversity_factor: share of connected load running at the same time, default 0.8
        power_factor: for kVA, default 0.85
        air_margin: margin on compressed air for leaks and growth, default 1.3
    """
    tot = {"power_kw": 0.0, "air_NL_min": 0.0, "water_L_h": 0.0, "steam_kg_h": 0.0}
    for m in machines:
        q = m.get("qty", 1)
        for k in tot:
            tot[k] += float(m.get(k, 0) or 0) * q
    demand_kw = tot["power_kw"] * diversity_factor
    return {"connected_load_kW": round(tot["power_kw"], 2), "demand_load_kW": round(demand_kw, 2),
            "transformer_kVA_min": round(demand_kw / power_factor, 1),
            "compressed_air_NL_min": round(tot["air_NL_min"] * air_margin, 1),
            "compressor_m3_min": round(tot["air_NL_min"] * air_margin / 1000, 2),
            "water_m3_h": round(tot["water_L_h"] / 1000, 2), "steam_kg_h": round(tot["steam_kg_h"], 1)}
