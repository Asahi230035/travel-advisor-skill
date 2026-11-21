"""Deterministic balanced budget modeling & transit-pass break-even calculator.

Never invents live prices or universal percentages. Caller supplies fixed costs,
trip-specific baseline shares, or itemized leg fares gathered by the host agent.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import math

from .common import InputError, decimal_money, positive_int, require_dict, require_list

INTENSITY = {
    'none': (1.0, 0.0),
    'slight': (1.15, 0.04),
    'moderate': (1.4, 0.08),
    'strong': (1.8, 0.12),
    'explicit': (2.5, 0.18),
}


def _cash_cents(value, name, allow_zero=True):
    dec = decimal_money(value, name, allow_zero=allow_zero)
    return int((dec * 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def _share(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise InputError(f'{label}: expected share in [0, 1]')
    return float(value)


def _round_largest_remainder(total_cents, shares):
    keys = list(shares)
    exact = {key: total_cents * shares[key] for key in keys}
    result = {key: math.floor(exact[key]) for key in keys}
    rest = total_cents - sum(result.values())
    for key in sorted(keys, key=lambda k: (-(exact[k] - result[k]), k))[:rest]:
        result[key] += 1
    return result


def _money(cents):
    return round(cents / 100, 2)


def allocate(payload):
    require_dict(payload)
    total = _cash_cents(payload.get('total_budget'), 'total_budget', allow_zero=False)
    fixed_input = payload.get('fixed_costs', {})
    require_dict(fixed_input, 'fixed_costs')
    fixed = {key: _cash_cents(value, f'fixed_costs.{key}') for key, value in fixed_input.items()}
    fixed_total = sum(fixed.values())

    if 'reserve_amount' in payload:
        reserve = _cash_cents(payload['reserve_amount'], 'reserve_amount')
    else:
        reserve = round(total * _share(payload.get('reserve_ratio', 0.10), 'reserve_ratio'))

    envelope = total - fixed_total - reserve
    if envelope < 0:
        raise InputError('fixed costs + reserve exceed total budget')

    baselines = payload.get('baseline_shares')
    if not isinstance(baselines, dict) or not baselines:
        raise InputError('trip-specific baseline_shares are required')
    base = {key: _share(value, f'baseline_shares.{key}') for key, value in baselines.items()}
    if not math.isclose(sum(base.values()), 1.0, abs_tol=1e-8):
        raise InputError('baseline_shares must total 1.0')

    minimum_input = payload.get('minimum_shares', {})
    require_dict(minimum_input, 'minimum_shares')
    if set(minimum_input) - set(base):
        raise InputError('minimum_shares includes unknown categories')
    minima = {key: _share(minimum_input.get(key, base[key] * 0.65), f'minimum_shares.{key}') for key in base}
    if any(minima[key] > base[key] for key in base):
        raise InputError('minimum shares cannot exceed balanced baseline')
    if sum(minima.values()) > 1.000000001:
        raise InputError('minimum shares exceed available flexible envelope')

    focus = payload.get('priorities', {})
    require_dict(focus, 'priorities')
    if set(focus) - set(base):
        raise InputError('priorities must reference known categories')

    multiplier = {}
    cap = 0.0
    for key in base:
        level = focus.get(key, 'none')
        if level not in INTENSITY:
            raise InputError(f'unknown preference intensity: {level}')
        multiplier[key] = INTENSITY[level][0]
        cap = max(cap, INTENSITY[level][1])

    target = {key: base[key] * multiplier[key] for key in base}
    bounds = {key: (max(minima[key], base[key] - cap), min(1.0, base[key] + cap)) for key in base}
    if sum(low for low, _ in bounds.values()) > 1.000000001 or sum(high for _, high in bounds.values()) < 0.999999999:
        raise InputError('preference bounds cannot form a full allocation')

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
    normalizer = sum(shares.values())
    shares = {key: value / normalizer for key, value in shares.items()}

    cents = _round_largest_remainder(envelope, shares)
    baseline_cents = _round_largest_remainder(envelope, base)

    travelers = positive_int(payload['travelers'], 'travelers') if 'travelers' in payload else None
    days = positive_int(payload['days'], 'days') if 'days' in payload else None

    # Build 3 scenario tiers around the flexible envelope (keeping fixed costs constant).
    tight_env = round(envelope * 0.85)
    upgraded_env = round(envelope * 1.25)
    tight_cats = _round_largest_remainder(tight_env, shares)
    upgraded_cats = _round_largest_remainder(upgraded_env, shares)

    def _scenario_block(env_cents, cat_cents, res_cents):
        scen_total = fixed_total + res_cents + env_cents
        block = {
            'total': _money(scen_total),
            'fixed_total': _money(fixed_total),
            'reserve': _money(res_cents),
            'flexible_total': _money(env_cents),
            'categories': {k: _money(cat_cents[k]) for k in base},
        }
        if travelers:
            block['per_person'] = round(scen_total / 100 / travelers, 2)
        if days:
            block['per_day'] = round(scen_total / 100 / days, 2)
        if travelers and days:
            block['per_person_per_day'] = round(scen_total / 100 / travelers / days, 2)
        return block

    result = {
        'task': 'budget',
        'currency': payload.get('currency', 'CNY'),
        'budget_total': _money(total),
        'travelers': travelers,
        'days': days,
        'fixed_costs': {key: _money(value) for key, value in fixed.items()},
        'reserve': _money(reserve),
        'flexible_envelope': _money(envelope),
        'balanced_baseline': {key: _money(baseline_cents[key]) for key in base},
        'preference_adjusted': {key: _money(cents[key]) for key in base},
        'delta': {key: _money(cents[key] - baseline_cents[key]) for key in base},
        'scenarios': {
            'tight': _scenario_block(tight_env, tight_cats, reserve),
            'balanced': _scenario_block(envelope, cents, reserve),
            'upgraded': _scenario_block(upgraded_env, upgraded_cats, round(reserve * 1.1)),
        },
        'sum_check': _money(fixed_total + reserve + sum(cents.values())),
        'status': 'illustrative_allocation_not_live_quote',
    }
    if travelers:
        result['per_person_budget'] = round(total / 100 / travelers, 2)
    if days:
        result['per_day_budget'] = round(total / 100 / days, 2)
    return result


def pass_check(payload):
    """Compare a transit pass / city card against itemized point-to-point fares."""
    require_dict(payload)
    pass_name = payload.get('pass_name') or 'Transit Pass'
    currency = payload.get('currency', 'JPY')
    pass_price = decimal_money(payload.get('pass_price'), 'pass_price', allow_zero=False)
    travelers = positive_int(payload.get('travelers', 1), 'travelers')
    legs = require_list(payload.get('legs'), 'legs', nonempty=True)

    p2p_total = Decimal('0.00')
    pass_extra_surcharges = Decimal('0.00')
    excluded_total = Decimal('0.00')
    covered_count = 0
    unverified_legs = []
    leg_summaries = []

    for idx, leg in enumerate(legs):
        require_dict(leg, f'legs[{idx}]')
        name = leg.get('name') or f'Leg {idx + 1}'
        fare = decimal_money(leg.get('single_fare'), f'legs[{idx}].single_fare')
        covered = leg.get('covered', True)
        if not isinstance(covered, bool):
            raise InputError(f'legs[{idx}].covered must be boolean')
        surcharge = decimal_money(leg.get('pass_surcharge', 0), f'legs[{idx}].pass_surcharge')
        verified = leg.get('verified', False) is True

        p2p_total += fare
        if covered:
            covered_count += 1
            pass_extra_surcharges += surcharge
        else:
            excluded_total += fare

        if not verified:
            unverified_legs.append(name)

        leg_summaries.append({
            'name': name,
            'single_fare': float(fare),
            'covered': covered,
            'pass_surcharge': float(surcharge) if covered else 0.0,
            'verified': verified,
        })

    pass_effective_total = pass_price + pass_extra_surcharges + excluded_total
    savings = p2p_total - pass_effective_total
    ratio = float((p2p_total - excluded_total) / (pass_price + pass_extra_surcharges)) if (pass_price + pass_extra_surcharges) > 0 else 0.0

    if unverified_legs:
        verdict = 'provisional_unverified_fares'
    elif savings >= pass_price * Decimal('0.08'):
        verdict = 'worth_it'
    elif savings >= -(pass_price * Decimal('0.05')):
        verdict = 'marginal_check_convenience'
    else:
        verdict = 'buy_point_to_point'

    return {
        'task': 'pass_check',
        'pass_name': pass_name,
        'currency': currency,
        'travelers': travelers,
        'per_person': {
            'point_to_point_total': float(p2p_total),
            'pass_price': float(pass_price),
            'pass_surcharges': float(pass_extra_surcharges),
            'excluded_legs_total': float(excluded_total),
            'pass_effective_total': float(pass_effective_total),
            'net_savings_with_pass': float(savings),
            'break_even_ratio': round(ratio, 3),
        },
        'group_total': {
            'point_to_point_total': float((p2p_total * travelers).quantize(Decimal('0.01'))),
            'pass_effective_total': float((pass_effective_total * travelers).quantize(Decimal('0.01'))),
            'net_savings_with_pass': float((savings * travelers).quantize(Decimal('0.01'))),
        },
        'covered_legs': covered_count,
        'total_legs': len(legs),
        'unverified_legs': unverified_legs,
        'legs': leg_summaries,
        'verdict': verdict,
        'caveats': [
            'Verify seat-reservation limits, non-covered express trains/private lines, and consecutive-day activation rules on the official operator site.',
            'If fares are unverified, treat this comparison as provisional.',
        ],
    }
