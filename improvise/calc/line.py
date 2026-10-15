"""Line design calculations: takt time, machine count, bottleneck, line balancing."""

from __future__ import annotations

import math

from ..tools import tool


@tool
def takt_time(demand_units: float, shifts: int, hours_per_shift: float, break_min_per_shift: float = 0) -> dict:
    """Takt time (seconds per unit) needed to meet a demand over one production day.

    Args:
        demand_units: units required per day
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
def machines_required(target_rate_per_hour: float, machine_rated_per_hour: float, expected_oee: float = 0.85) -> dict:
    """Number of identical machines needed in parallel to reach a target output rate.

    Args:
        target_rate_per_hour: required good output per hour
        machine_rated_per_hour: nameplate speed of one machine per hour
        expected_oee: expected OEE as a fraction (0-1), default 0.85
    """
    if not 0 < expected_oee <= 1:
        raise ValueError("expected_oee must be between 0 and 1")
    effective = machine_rated_per_hour * expected_oee
    n = math.ceil(target_rate_per_hour / effective)
    return {
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
