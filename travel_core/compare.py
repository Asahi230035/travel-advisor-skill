"""Like-for-like travel quote comparison with surcharge breakdown & optional FX normalization.

Two nominal prices are never placed in a shared price ranking unless dates,
occupancy, product entitlements, mandatory surcharges, and currencies are aligned.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
import json

from .common import (
    InputError,
    bounded_number,
    clock,
    date_value,
    decimal_money,
    decimal_rate,
    require_dict,
    require_list,
    unique_ids,
)

DIMENSIONS = ('interest', 'comfort', 'convenience', 'experience', 'time_efficiency', 'crowd')

BASE_KEYS = {
    'hotel': ('checkin', 'checkout', 'guests', 'rooms', 'room_type', 'currency'),
    'transport': (
        'departure_date', 'from', 'to', 'travelers', 'currency',
        'transport_mode', 'departure_time', 'arrival_time', 'transfers', 'route_pattern',
    ),
    'restaurant': ('service_date', 'people', 'currency'),
    'activity': ('service_date', 'people', 'currency'),
}

TERM_KEYS = {
    'hotel': ('breakfast', 'cancellation', 'membership_required', 'payment_terms'),
    'transport': ('fare_class', 'refund_policy', 'change_policy', 'baggage_allowance'),
    'restaurant': ('menu_basis',),
    'activity': ('ticket_type', 'refund_policy'),
}


def _filled(v):
    return v is not None and v != ''


def _quantize(dec: Decimal) -> float:
    return float(dec.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


def _parse_surcharges(raw):
    """Parse optional mandatory_surcharges (dict of label->amount or list of {name, amount})."""
    if raw is None:
        return {}, Decimal('0.00')
    breakdown = {}
    total = Decimal('0.00')
    if isinstance(raw, dict):
        for k, v in raw.items():
            amt = decimal_money(v, f'mandatory_surcharges.{k}')
            breakdown[str(k)] = _quantize(amt)
            total += amt
        return breakdown, total
    if isinstance(raw, list):
        for idx, item in enumerate(raw):
            require_dict(item, f'mandatory_surcharges[{idx}]')
            name = item.get('name') or f'fee_{idx + 1}'
            amt = decimal_money(item.get('amount'), f'mandatory_surcharges[{idx}].amount')
            breakdown[str(name)] = _quantize(amt)
            total += amt
        return breakdown, total
    raise InputError('mandatory_surcharges must be an object or array')


def _read_quote(q, kind):
    if not isinstance(q, dict):
        return None, None, ['missing_quote'], {}, Decimal('0.00'), None, None

    keys = BASE_KEYS[kind] + TERM_KEYS[kind]
    sig = {key: q.get(key) for key in keys}
    issues = ['missing_' + k for k, v in sig.items() if not _filled(v)]

    nights = None
    if kind == 'hotel' and _filled(q.get('checkin')) and _filled(q.get('checkout')):
        ci = date_value(q['checkin'], 'checkin')
        co = date_value(q['checkout'], 'checkout')
        if co <= ci:
            issues.append('checkout_not_after_checkin')
        else:
            nights = (co - ci).days

    if kind == 'hotel' and 'membership_required' in q and not isinstance(q['membership_required'], bool):
        issues.append('invalid_membership_required')

    party_size = None
    for field in ('guests', 'rooms', 'travelers', 'people'):
        if field in q:
            if type(q[field]) is not int or q[field] < 1:
                issues.append('invalid_' + field)
            elif field != 'rooms':
                party_size = q[field]

    if kind == 'transport' and 'transfers' in q and (type(q['transfers']) is not int or q['transfers'] < 0):
        issues.append('invalid_transfers')

    if kind == 'transport':
        for field in ('departure_time', 'arrival_time'):
            if _filled(q.get(field)):
                clock(q[field], field)

    for field in ('checkin', 'checkout', 'departure_date', 'service_date'):
        if _filled(q.get(field)):
            date_value(q[field], field)

    for field in sig:
        if isinstance(sig[field], (dict, list)):
            issues.append('invalid_' + field)

    surcharges, surcharge_total = _parse_surcharges(q.get('mandatory_surcharges'))

    if 'all_in_price' in q:
        price = decimal_money(q['all_in_price'], 'all_in_price')
        # If caller supplied separate unincluded mandatory surcharges (e.g. on-site city tax), add them clearly.
        if q.get('surcharges_excluded_from_all_in') is True and surcharge_total > 0:
            price = price + surcharge_total
    elif 'base_price' in q and q.get('price_basis') == 'all_in_total':
        price = decimal_money(q['base_price'], 'base_price') + surcharge_total
    else:
        price = None
        issues.append('missing_all_in_price')

    if q.get('price_basis') != 'all_in_total':
        issues.append('not_comparable_price_basis')
    if q.get('taxes_included') is not True or q.get('mandatory_fees_included') is not True:
        issues.append('taxes_or_mandatory_fees_unknown')

    return price, sig, issues, surcharges, surcharge_total, nights, party_size


def compare(payload):
    require_dict(payload)
    kind = payload.get('kind', 'hotel')
    if kind not in BASE_KEYS:
        raise InputError('kind must be hotel/restaurant/transport/activity')
    options = require_list(payload.get('options'), 'options', nonempty=True)
    unique_ids(options, 'options')
    if len(options) < 2:
        raise InputError('comparison requires at least 2 options')

    target_currency = payload.get('target_currency')
    fx_rates_raw = payload.get('fx_rates') or {}
    fx_as_of = payload.get('fx_as_of')
    if target_currency is not None:
        if not isinstance(target_currency, str) or not target_currency.strip():
            raise InputError('target_currency must be a nonempty string')
        target_currency = target_currency.strip().upper()
        require_dict(fx_rates_raw, 'fx_rates')
        if fx_as_of is not None:
            date_value(fx_as_of, 'fx_as_of')
    fx_rates = {str(k).strip().upper(): decimal_rate(v, f'fx_rates.{k}') for k, v in fx_rates_raw.items()}

    results = []
    groups = {}
    for option in options:
        require_dict(option, 'option')
        q = option.get('quote')
        price, signature, issues, surcharges, surcharge_total, nights, party_size = _read_quote(q, kind)
        signals = require_dict(option.get('signals', {}), 'signals')
        if set(signals) - set(DIMENSIONS):
            raise InputError('unsupported signals (must be shared comparison dimensions)')
        normalized_signals = {k: bounded_number(v, 'signals.' + k) for k, v in signals.items()}
        features = require_dict(option.get('features', {}), 'features')

        orig_currency = (q.get('currency').strip().upper() if isinstance(q, dict) and isinstance(q.get('currency'), str) and q.get('currency').strip() else None)
        effective_currency = orig_currency
        effective_price = price
        fx_converted = False
        fx_rate_used = None

        if target_currency and orig_currency and price is not None:
            if orig_currency == target_currency:
                effective_currency = target_currency
            elif orig_currency in fx_rates:
                if fx_as_of is None:
                    issues.append('missing_fx_as_of_date')
                else:
                    fx_rate_used = float(fx_rates[orig_currency])
                    effective_price = (price * fx_rates[orig_currency]).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                    effective_currency = target_currency
                    fx_converted = True
            else:
                issues.append(f'missing_fx_rate_{orig_currency}_to_{target_currency}')

        group_signature = dict(signature) if isinstance(signature, dict) else {}
        if fx_converted:
            group_signature['currency'] = effective_currency

        per_night = _quantize(effective_price / nights) if (effective_price is not None and nights) else None
        per_person = _quantize(effective_price / party_size) if (effective_price is not None and party_size) else None

        entry = {
            'id': option['id'],
            'name': option.get('name') or option['id'],
            'all_in_price': _quantize(effective_price) if effective_price is not None else None,
            'currency': effective_currency,
            'original_price': _quantize(price) if price is not None else None,
            'original_currency': orig_currency,
            'fx_converted': fx_converted,
            'fx_rate_used': fx_rate_used,
            'fx_as_of': fx_as_of if fx_converted else None,
            'per_night_price': per_night,
            'per_person_price': per_person,
            'mandatory_surcharges': surcharges,
            'surcharge_total': _quantize(surcharge_total),
            'quote_normalized': not issues,
            'price_comparable': False,
            'package_equivalent': False,
            'issues': list(issues),
            'signature': group_signature,
            'signals': normalized_signals,
            'features': features,
            'source': option.get('source'),
            'retrieved_at': option.get('retrieved_at'),
            'quote_conditions': {k: q.get(k) for k in TERM_KEYS[kind]} if isinstance(q, dict) else {},
            'evidence_status': option.get('evidence_status', 'unverified'),
            'comparison_group': None,
        }
        results.append(entry)
        if not issues:
            key = json.dumps(group_signature, sort_keys=True, ensure_ascii=False)
            groups.setdefault(key, []).append(entry)

    comparable_groups = []
    for index, entries in enumerate(groups.values(), start=1):
        group_id = f'group-{index}'
        for entry in entries:
            entry['comparison_group'] = group_id
        if len(entries) < 2:
            entries[0]['issues'].append('no_equivalent_quote_for_comparison')
            continue
        ranked = sorted(entries, key=lambda e: e['all_in_price'])
        comparable_groups.append({
            'group_id': group_id,
            'option_ids': [e['id'] for e in entries],
            'price_ranking_low_to_high': [e['id'] for e in ranked],
            'aligned_conditions': entries[0]['signature'],
        })
        for entry in entries:
            entry['price_comparable'] = True
            entry['package_equivalent'] = True

    ranking = comparable_groups[0]['price_ranking_low_to_high'] if len(comparable_groups) == 1 else []

    requested = payload.get('weights')
    if requested is not None:
        require_dict(requested, 'weights')
        if not requested or set(requested) - set(DIMENSIONS):
            raise InputError('unsupported weights')
        weights = {k: bounded_number(v, 'weights.' + k, 0, 1) for k, v in requested.items()}
        if abs(sum(weights.values()) - 1) > 1e-7:
            raise InputError('weights must sum to 1')
        for entry in results:
            if set(entry['signals']) != set(weights):
                entry['indicative_preference_score'] = None
                entry['issues'].append('missing_comparable_scoring_signals')
            else:
                entry['indicative_preference_score'] = round(sum(entry['signals'][k] * weights[k] for k in weights), 1)
                entry['score_basis'] = 'user_or_agent_supplied_rubric_not_independently_verified'

    dominated = []
    for group in comparable_groups:
        members = [e for e in results if e['id'] in group['option_ids']]
        for a in members:
            for b in members:
                if (
                    a is b
                    or not a['signals']
                    or set(a['signals']) != set(b['signals'])
                    or a['features'] != b['features']
                ):
                    continue
                if (
                    b['all_in_price'] <= a['all_in_price']
                    and all(b['signals'][k] >= a['signals'][k] for k in a['signals'])
                    and (
                        b['all_in_price'] < a['all_in_price']
                        or any(b['signals'][k] > a['signals'][k] for k in a['signals'])
                    )
                ):
                    dominated.append({'option_id': a['id'], 'dominated_by': b['id'], 'scope': 'supplied_metrics_only'})
                    break

    return {
        'task': 'compare',
        'kind': kind,
        'target_currency': target_currency,
        'fx_as_of': fx_as_of,
        'options': results,
        'comparable_option_ids': [e['id'] for e in results if e['price_comparable']],
        'comparable_groups': comparable_groups,
        'price_ranking_low_to_high': ranking,
        'dominated_options': dominated,
        'pending_normalization': [e['id'] for e in results if not e['quote_normalized']],
        'not_comparable': [e['id'] for e in results if not e['price_comparable']],
        'notes': [
            'A valid total price is not necessarily a comparable package.',
            'Price rankings appear only within identical dates, occupancy, currency, and benefit terms.',
            'Differences in breakfast, cancellation, transfers, baggage, or surcharges must be explained as trade-offs.',
            'FX conversion uses caller-supplied dated rates; bank/card spreads may still apply.',
        ],
    }
