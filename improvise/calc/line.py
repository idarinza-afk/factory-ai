"""Line design calculations: takt time, machine count, bottleneck, line balancing."""

from __future__ import annotations

import math

from ..tools import tool


@tool
def takt_time(demand_units: float, shifts: int, hours_per_shift: float, break_min_per_shift: float = 0) -> dict:
    """Takt time from a DAILY demand. If the demand is given per hour or per minute, use takt_from_rate instead.

    Args:
        demand_units: units required per DAY (not per hour)
        shifts: number of shifts per day
        hours_per_shift: paid hours per shift
        break_min_per_shift: planned breaks/meals/cleaning per shift in minutes
    """
    if demand_units <= 0:
        raise ValueError("demand_units must be > 0")
    available_s = shifts * (hours_per_shift * 3600 - break_min_per_shift * 60)
    if available_s <= 0:
        raise ValueError("no available time")
    takt = available_s / demand_units
    return {
        "available_time_s": round(available_s, 1),
        "takt_time_s": round(takt, 3),
        "required_rate_per_min": round(60 / takt, 2),
        "required_rate_per_hour": round(3600 / takt, 1),
    }


@tool
def takt_from_rate(rate_per_hour: float, units_per_pack: float = 1, shifts: int = 0, hours_per_shift: float = 0,
                   break_min_per_shift: float = 0) -> dict:
    """Takt time when the required rate is given per hour (e.g. 8,000 eggs/h); also packs per minute and daily output.

    Args:
        rate_per_hour: required good units per hour
        units_per_pack: units per tray/case/pack, default 1
        shifts: shifts per day (optional, for daily output)
        hours_per_shift: hours per shift (optional)
        break_min_per_shift: breaks per shift in minutes (optional)
    """
    if rate_per_hour <= 0:
        raise ValueError("rate_per_hour must be > 0")
    res = {"takt_time_s_per_unit": round(3600 / rate_per_hour, 3), "units_per_min": round(rate_per_hour / 60, 2),
           "packs_per_hour": round(rate_per_hour / units_per_pack, 1),
           "packs_per_min": round(rate_per_hour / units_per_pack / 60, 2),
           "takt_time_s_per_pack": round(3600 * units_per_pack / rate_per_hour, 2)}
    if shifts and hours_per_shift:
        hours = shifts * (hours_per_shift - break_min_per_shift / 60)
        res.update({"production_hours_per_day": round(hours, 2), "units_per_day": round(rate_per_hour * hours),
                    "packs_per_day": round(rate_per_hour * hours / units_per_pack)})
    return res


@tool
def machines_required(machine_rated_per_hour: float, target_rate_per_hour: float = 0, expected_oee: float = 0.85,
                      target_units_per_period: float = 0, period_hours: float = 0) -> dict:
    """Number of identical machines needed in parallel to reach a target output (per hour, or per shift/day).

    Args:
        machine_rated_per_hour: nameplate speed of one machine per hour
        target_rate_per_hour: required good output per hour (or give target_units_per_period + period_hours)
        expected_oee: expected OEE as a fraction (0-1), default 0.85
        target_units_per_period: required good output per shift or per day (alternative to the hourly rate)
        period_hours: productive hours in that shift/day
    """
    if not 0 < expected_oee <= 1:
        raise ValueError("expected_oee must be between 0 and 1")
    if not target_rate_per_hour:
        if not (target_units_per_period and period_hours):
            raise ValueError("give target_rate_per_hour, or target_units_per_period and period_hours")
        target_rate_per_hour = target_units_per_period / period_hours
    effective = machine_rated_per_hour * expected_oee
    n = math.ceil(target_rate_per_hour / effective)
    return {
        "target_rate_per_hour": round(target_rate_per_hour, 1),
        "effective_rate_per_machine": round(effective, 1),
        "machines": n,
        "installed_capacity_per_hour": round(n * effective, 1),
        "utilisation": round(target_rate_per_hour / (n * effective), 3),
    }


@tool
def line_capacity(stations: list[dict]) -> dict:
    """Find the bottleneck and real output of a serial line.

    Args:
        stations: list of {"name": str, "rate_per_hour": float, "oee": float (optional, default 1), "parallel": int (optional, default 1)}
    """
    if not stations:
        raise ValueError("stations is empty")
    rows = []
    for s in stations:
        eff = float(s["rate_per_hour"]) * float(s.get("oee", 1.0)) * int(s.get("parallel", 1))
        rows.append({"name": s["name"], "effective_rate_per_hour": round(eff, 1)})
    bottleneck = min(rows, key=lambda r: r["effective_rate_per_hour"])
    cap = bottleneck["effective_rate_per_hour"]
    for r in rows:
        r["load"] = round(cap / r["effective_rate_per_hour"], 3)
    return {"line_output_per_hour": cap, "bottleneck": bottleneck["name"], "stations": rows}


@tool
def line_balance(tasks: list[dict], cycle_time_s: float) -> dict:
    """Assign tasks to workstations with the Ranked Positional Weight method.

    Args:
        tasks: list of {"name": str, "time_s": float, "predecessors": [names]}
        cycle_time_s: target cycle time (usually the takt time) in seconds
    """
    by_name = {t["name"]: {**t, "predecessors": list(t.get("predecessors", []))} for t in tasks}
    for t in by_name.values():
        if t["time_s"] > cycle_time_s:
            raise ValueError(f"task {t['name']} ({t['time_s']} s) is longer than the cycle time - split it or parallelise")
        for p in t["predecessors"]:
            if p not in by_name:
                raise ValueError(f"unknown predecessor {p} of {t['name']}")

    succ: dict[str, list[str]] = {n: [] for n in by_name}
    for n, t in by_name.items():
        for p in t["predecessors"]:
            succ[p].append(n)

    memo: dict[str, float] = {}

    def weight(n: str) -> float:
        if n not in memo:
            seen, stack, total = set(), [n], 0.0
            while stack:
                x = stack.pop()
                if x in seen:
                    continue
                seen.add(x)
                total += by_name[x]["time_s"]
                stack.extend(succ[x])
            memo[n] = total
        return memo[n]

    order = sorted(by_name, key=weight, reverse=True)
    done: set[str] = set()
    stations: list[dict] = []
    while len(done) < len(by_name):
        st, load = [], 0.0
        progress = True
        while progress:
            progress = False
            for n in order:
                t = by_name[n]
                if n in done or n in st:
                    continue
                if all(p in done or p in st for p in t["predecessors"]) and load + t["time_s"] <= cycle_time_s + 1e-9:
                    st.append(n)
                    load += t["time_s"]
                    progress = True
                    break
        if not st:
            raise ValueError("could not assign tasks - check for precedence cycles")
        done.update(st)
        stations.append({"station": len(stations) + 1, "tasks": st, "load_s": round(load, 2), "idle_s": round(cycle_time_s - load, 2)})

    work = sum(t["time_s"] for t in by_name.values())
    n = len(stations)
    eff = work / (n * cycle_time_s)
    return {
        "stations": stations,
        "workstations": n,
        "theoretical_min_stations": math.ceil(work / cycle_time_s),
        "line_efficiency": round(eff, 3),
        "balance_delay": round(1 - eff, 3),
    }


@tool
def buffer_size(downstream_rate_per_min: float, upstream_stop_min: float, safety_factor: float = 1.2) -> dict:
    """Accumulation buffer needed so a downstream machine keeps running while upstream stops.

    Args:
        downstream_rate_per_min: consumption rate of the downstream machine (units/min)
        upstream_stop_min: typical upstream short stop to ride through (min)
        safety_factor: margin multiplier, default 1.2
    """
    units = math.ceil(downstream_rate_per_min * upstream_stop_min * safety_factor)
    return {"buffer_units": units}


@tool
def product_spacing(product_length_mm: float, gap_mm: float, rate_per_min: float, infeed_pitch_mm: float = 0) -> dict:
    """Create gaps between products by a speed step-up from an infeed conveyor to a faster conveyor.

    Args:
        product_length_mm: product length in the direction of travel
        gap_mm: required gap between products after the transfer
        rate_per_min: products per minute
        infeed_pitch_mm: product pitch on the infeed (0 = products touching, pitch = product length)
    """
    p_in = infeed_pitch_mm or product_length_mm
    p_out = product_length_mm + gap_mm
    if p_out <= p_in:
        raise ValueError("the required pitch is not larger than the infeed pitch - no speed-up needed")
    v_in = rate_per_min * p_in / 1000          # m/min
    v_out = rate_per_min * p_out / 1000
    return {"infeed_speed_m_per_min": round(v_in, 2), "outfeed_speed_m_per_min": round(v_out, 2),
            "speed_ratio": round(v_out / v_in, 3), "outfeed_pitch_mm": p_out,
            "next_step": (f"If motors are needed: call conveyor_sizing for EACH conveyor - infeed with pitch_mm={p_in:g}, "
                          f"outfeed with pitch_mm={p_out:g}, same rate_per_min={rate_per_min:g}."),
            "notes": ["each product is pulled away once its centre of gravity passes onto the faster belt",
                      "keep the transfer short (dead plate or nose-over) so products do not tip",
                      "use a VFD on the faster conveyor (at least) to fine-tune the ratio on site",
                      "photo-eye after the transfer measures gap = sensor OFF time x outfeed speed to verify spacing"]}
