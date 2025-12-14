"""
Core cashflow and risk metric definitions.
Deterministic, static, one-period stress-testing framework.
Includes stress-grid generation utilities + calibration helpers.
"""

from __future__ import annotations

import numpy as np


def net_operating_income(revenue: float, operating_cost_ratio: float) -> float:
    """NOI = revenue * (1 - operating_cost_ratio)"""
    return revenue * (1.0 - operating_cost_ratio)


def interest_cost(interest_rate: float, debt_balance: float) -> float:
    """Interest-only debt service"""
    return interest_rate * debt_balance


def net_cashflow(
    revenue: float,
    operating_cost_ratio: float,
    interest_rate: float,
    debt_balance: float,
) -> float:
    """CF = revenue - operating_costs - interest_cost"""
    operating_costs = revenue * operating_cost_ratio
    return revenue - operating_costs - interest_cost(interest_rate, debt_balance)


def dscr(
    revenue: float,
    operating_cost_ratio: float,
    interest_rate: float,
    debt_balance: float,
) -> float:
    """DSCR = (revenue - operating_costs) / interest_cost"""
    interest = interest_cost(interest_rate, debt_balance)
    if interest <= 0:
        raise ValueError("Interest cost must be positive for DSCR.")
    return (revenue * (1.0 - operating_cost_ratio)) / interest


def analytical_break_even_occupancy(
    interest_rate: float,
    operating_cost_ratio: float,
    debt_balance: float,
    base_rent: float = 1.0,
) -> float:
    """
    Analytical break-even occupancy (DSCR = 1)

    occupancy* = (r * D) / ((1 - c) * rent)
    """
    return (interest_rate * debt_balance) / ((1.0 - operating_cost_ratio) * base_rent)


def theta_from_yield_ltv(gross_yield: float, ltv: float) -> float:
    """
    If annual_rent ≈ gross_yield * price and debt ≈ ltv * price, then:
      theta = rent/debt ≈ gross_yield / ltv
    """
    if ltv <= 0:
        raise ValueError("ltv must be > 0")
    return float(gross_yield) / float(ltv)


# -----------------------------
# Stress grid generation
# -----------------------------

def _inclusive_arange(start: float, stop: float, step: float, decimals: int = 10) -> np.ndarray:
    """
    Inclusive range generator for floats (stable endpoints).
    Returns values from start..stop inclusive (if close within tolerance).
    """
    if step <= 0:
        raise ValueError("step must be > 0")

    n = int(np.floor((stop - start) / step + 1e-12)) + 1
    vals = start + step * np.arange(n, dtype=float)

    vals = vals[vals <= stop + 1e-12]
    vals = np.round(vals, decimals=decimals)

    if vals.size == 0:
        vals = np.array([np.round(start, decimals=decimals)], dtype=float)

    # Ensure stop included if nearly equal
    if abs(vals[-1] - stop) > 1e-8 and stop >= vals[-1] + 1e-8:
        vals = np.append(vals, np.round(stop, decimals=decimals))

    return np.unique(vals)


def generate_rate_shocks_bp(assumptions: dict) -> np.ndarray:
    """
    Returns array of rate shocks in basis points.

    Supports:
    - interest_rate_stress: {start_bp, stop_bp, step_bp}
    - legacy: interest_rate_stress: {shocks_bp: [...]}
    """
    ir = assumptions.get("interest_rate_stress", {})
    if "shocks_bp" in ir:
        return np.array(sorted(ir["shocks_bp"]), dtype=float)

    start_bp = float(ir["start_bp"])
    stop_bp = float(ir["stop_bp"])
    step_bp = float(ir["step_bp"])
    return _inclusive_arange(start_bp, stop_bp, step_bp, decimals=6)


def generate_occupancy_grid(assumptions: dict) -> np.ndarray:
    """
    Returns array of occupancy multipliers.

    Supports:
    - revenue_stress: {occupancy_range: {start, stop, step}}
    - legacy: revenue_stress: {occupancy_multipliers: {...}}
    """
    rs = assumptions.get("revenue_stress", {})
    if "occupancy_multipliers" in rs:
        return np.array(sorted(rs["occupancy_multipliers"].values()), dtype=float)

    occ = rs["occupancy_range"]
    start = float(occ["start"])
    stop = float(occ["stop"])
    step = float(occ["step"])
    return _inclusive_arange(start, stop, step, decimals=6)
