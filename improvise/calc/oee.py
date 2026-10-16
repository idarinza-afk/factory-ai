"""OEE = Availability x Performance x Quality."""

from __future__ import annotations

from ..tools import tool


@tool
def oee(planned_time_min: float, downtime_min: float, ideal_cycle_time_s: float, total_count: int, good_count: int,
        planned_breaks_min: float = 0) -> dict:
    """Overall Equipment Effectiveness with its three factors and the main loss.

    Args:
        planned_time_min: shift / period length in minutes (e.g. 8 h = 480)
        downtime_min: UNPLANNED stop time in minutes
        ideal_cycle_time_s: ideal seconds per unit at rated speed
        total_count: total units produced
        good_count: good units (first pass); if only rejects are given, good = total - rejects
        planned_breaks_min: planned breaks, meals, cleaning and meetings in the period - subtracted from the period
    """
    planned_time_min = planned_time_min - planned_breaks_min
    if planned_time_min <= 0:
        raise ValueError("planned_time_min must be > 0")
    if good_count > total_count:
        raise ValueError("good_count cannot exceed total_count")
    run_min = planned_time_min - downtime_min
    if run_min <= 0:
        raise ValueError("downtime is greater than planned time")
    a = run_min / planned_time_min
    p = (ideal_cycle_time_s * total_count) / (run_min * 60)
    q = good_count / total_count if total_count else 0.0
    factors = {"availability": a, "performance": p, "quality": q}
    worst = min(factors, key=factors.get)
    return {
        **{k: round(v, 4) for k, v in factors.items()},
        "oee": round(a * p * q, 4),
        "planned_production_time_min": round(planned_time_min, 1),
        "biggest_loss": worst,
        "warning": "performance > 100%: ideal cycle time is probably wrong" if p > 1 else "",
    }
