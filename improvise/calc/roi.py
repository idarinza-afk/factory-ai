"""Investment evaluation: payback, NPV, IRR."""

from __future__ import annotations

from ..tools import tool


def _npv(rate: float, flows: list[float]) -> float:
    return sum(cf / (1 + rate) ** i for i, cf in enumerate(flows))


def _irr(flows: list[float]) -> float | None:
    lo, hi = -0.99, 10.0
    f_lo, f_hi = _npv(lo, flows), _npv(hi, flows)
    if f_lo * f_hi > 0:
        return None
    for _ in range(200):
        mid = (lo + hi) / 2
        f_mid = _npv(mid, flows)
        if abs(f_mid) < 1e-7:
            break
        if f_lo * f_mid < 0:
            hi, f_hi = mid, f_mid
        else:
            lo, f_lo = mid, f_mid
    return (lo + hi) / 2


@tool
def roi(investment: float, annual_net_cashflow: list[float], discount_rate: float = 0.08) -> dict:
    """Payback period, NPV and IRR of a machine or line investment.

    Args:
        investment: upfront investment (positive number)
        annual_net_cashflow: net cash benefit for each year, e.g. [1200000, 1200000, 1300000]
        discount_rate: discount rate as a fraction, default 0.08
    """
    if investment <= 0:
        raise ValueError("investment must be > 0")
    flows = [-investment] + [float(x) for x in annual_net_cashflow]
    cum, payback = -investment, None
    for year, cf in enumerate(annual_net_cashflow, start=1):
        if cf > 0 and cum + cf >= 0 and payback is None:
            payback = year - 1 + (-cum) / cf
        cum += cf
    irr = _irr(flows)
    return {
        "payback_years": round(payback, 2) if payback is not None else None,
        "npv": round(_npv(discount_rate, flows), 2),
        "irr": round(irr, 4) if irr is not None else None,
        "total_net_cashflow": round(sum(flows), 2),
    }
