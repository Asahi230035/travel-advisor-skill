#!/usr/bin/env python3
"""Deterministic, balanced-first budget allocation demonstration.

Inputs are hypothetical/verified budget assumptions, NOT live quotes.
The model allocates only the flexible envelope after fixed costs and contingency.
The category baseline must be supplied for the trip; no universal percentages.
"""
from __future__ import annotations

import json
import math
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

INTENSITY = {"none": (1.0, 0.0), "slight": (1.15, 0.04), "moderate": (1.4, 0.08), "strong": (1.8, 0.12), "explicit": (2.5, 0.18)}


def _cash_cents(value, name):
    if isinstance(value, bool):
        raise ValueError(f"{name}: invalid money")
    try:
        amount = Decimal(str(value))
    except Exception as exc:
        raise ValueError(f"{name}: invalid money") from exc
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{name}: expected nonnegative finite amount")
    return int((amount * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _share(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{label}: expected share 0..1")
    return float(value)


def _round_largest_remainder(total_cents, shares):
    keys = list(shares)
    exact = {key: total_cents * shares[key] for key in keys}
    result = {key: math.floor(exact[key]) for key in keys}
    rest = total_cents - sum(result.values())
    for key in sorted(keys, key=lambda k: (-(exact[k] - result[k]), k))[:rest]:
        result[key] += 1
    return result


def allocate(payload):
    total = _cash_cents(payload["total_budget"], "total_budget")
    if total == 0:
        raise ValueError("total_budget must be positive")
    fixed_input = payload.get("fixed_costs", {})
    if not isinstance(fixed_input, dict):
        raise ValueError("fixed_costs must be an object")
    fixed = {key: _cash_cents(value, f"fixed_costs.{key}") for key, value in fixed_input.items()}
    fixed_total = sum(fixed.values())
    if "reserve_amount" in payload:
        reserve = _cash_cents(payload["reserve_amount"], "reserve_amount")
    else:
        reserve = round(total * _share(payload.get("reserve_ratio", 0.10), "reserve_ratio"))
    envelope = total - fixed_total - reserve
    if envelope < 0:
        raise ValueError("fixed costs + reserve exceed total budget")
    baselines = payload.get("baseline_shares")
    if not isinstance(baselines, dict) or not baselines:
        raise ValueError("trip-specific baseline_shares are required")
    base = {key: _share(value, f"baseline_shares.{key}") for key, value in baselines.items()}
    if not math.isclose(sum(base.values()), 1.0, abs_tol=1e-8):
        raise ValueError("baseline_shares must total 1.0")
    minimum_input = payload.get("minimum_shares", {})
    if set(minimum_input) - set(base):
        raise ValueError("minimum_shares includes unknown categories")
    minima = {key: _share(minimum_input.get(key, base[key] * 0.65), f"minimum_shares.{key}") for key in base}
    if any(minima[key] > base[key] for key in base):
        raise ValueError("minimum shares cannot exceed balanced baseline")
    if sum(minima.values()) > 1.000000001:
        raise ValueError("minimum shares exceed available flexible envelope")
    focus = payload.get("priorities", {})
    if not isinstance(focus, dict) or set(focus) - set(base):
        raise ValueError("priorities must reference known categories")
    multiplier = {}
    cap = 0.0
    for key in base:
        level = focus.get(key, "none")
        if level not in INTENSITY:
            raise ValueError(f"unknown preference intensity: {level}")
        multiplier[key] = INTENSITY[level][0]
        cap = max(cap, INTENSITY[level][1])
    target = {key: base[key] * multiplier[key] for key in base}
    bounds = {key: (max(minima[key], base[key] - cap), min(1.0, base[key] + cap)) for key in base}
    if sum(low for low, high in bounds.values()) > 1.000000001 or sum(high for low, high in bounds.values()) < 0.999999999:
        raise ValueError("preference bounds cannot form a full allocation")
    lo, hi = 0.0, 1.0
    while sum(min(bounds[k][1], max(bounds[k][0], target[k] * hi)) for k in base) < 1:
        hi *= 2
    for _ in range(100):
        mid = (lo + hi) / 2
        got = sum(min(bounds[k][1], max(bounds[k][0], target[k] * mid)) for k in base)
        if got < 1:
            lo = mid
        else:
            hi = mid
    shares = {key: min(bounds[key][1], max(bounds[key][0], target[key] * hi)) for key in base}
    # Normalize tiny floating-point residuals; exact cents are enforced below.
    normalizer = sum(shares.values())
    shares = {key: value / normalizer for key, value in shares.items()}
    cents = _round_largest_remainder(envelope, shares)
    baseline_cents = _round_largest_remainder(envelope, base)
    def money(v):
        return round(v / 100, 2)
    return {
        "currency": payload.get("currency", "CNY"),
        "budget_total": money(total),
        "fixed_costs": {key: money(value) for key, value in fixed.items()},
        "reserve": money(reserve),
        "flexible_envelope": money(envelope),
        "balanced_baseline": {key: money(baseline_cents[key]) for key in base},
        "preference_adjusted": {key: money(cents[key]) for key in base},
        "delta": {key: money(cents[key] - baseline_cents[key]) for key in base},
        "sum_check": money(sum(fixed.values()) + reserve + sum(cents.values())),
        "status": "illustrative_allocation_not_live_quote"
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/allocate_budget.py examples/budget_demo.json")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(allocate(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
