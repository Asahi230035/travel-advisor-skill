"""Conservative travel-quote comparison, without invented prices or ratings.

Price validation and product/package equivalence are distinct. Two nominal
prices are never described as an apples-to-apples ranking unless the terms
needed for that product category are known and aligned.
"""
from __future__ import annotations
import json
from .common import InputError, require_dict, require_list, unique_ids, decimal_money, bounded_number, date_value

DIMENSIONS = ('interest', 'comfort', 'convenience', 'experience', 'time_efficiency', 'crowd')

BASE_KEYS = {
    'hotel': ('checkin', 'checkout', 'guests', 'rooms', 'room_type', 'currency'),
    'transport': ('departure_date', 'from', 'to', 'travelers', 'currency',
                  'transport_mode', 'departure_time', 'arrival_time', 'transfers', 'route_pattern'),
    'restaurant': ('service_date', 'people', 'currency'),
    'activity': ('service_date', 'people', 'currency'),
}
# Hotel board / cancellation / member eligibility can change real value.
# Other categories are compared on like-for-like packages only when the
# provider has supplied a concrete ticket/menu product description.
TERM_KEYS = {
    'hotel': ('breakfast', 'cancellation', 'membership_required', 'payment_terms'),
    'transport': ('fare_class', 'refund_policy', 'change_policy', 'baggage_allowance'),
    'restaurant': ('menu_basis',),
    'activity': ('ticket_type', 'refund_policy'),
}


def _filled(v):
    return v is not None and v != ''


def _check_signature(q, kind):
    keys = BASE_KEYS[kind] + TERM_KEYS[kind]
    return {key: q.get(key) for key in keys}


def _read_quote(q, kind):
    if not isinstance(q, dict):
        return None, None, ['missing_quote']
    sig = _check_signature(q, kind)
    issues = ['missing_' + k for k, v in sig.items() if not _filled(v)]
    if kind == 'hotel' and _filled(q.get('checkin')) and _filled(q.get('checkout')):
        if date_value(q['checkout'], 'checkout') <= date_value(q['checkin'], 'checkin'):
            issues.append('checkout_not_after_checkin')
    if kind == 'hotel' and 'membership_required' in q and not isinstance(q['membership_required'], bool):
        issues.append('invalid_membership_required')
    for field in ('guests', 'rooms', 'travelers', 'people'):
        if field in q and (type(q[field]) is not int or q[field] < 1):
            issues.append('invalid_' + field)
    if kind == 'transport' and 'transfers' in q and (type(q['transfers']) is not int or q['transfers'] < 0):
        issues.append('invalid_transfers')
    if kind == 'transport':
        from .common import clock
        for field in ('departure_time', 'arrival_time'):
            if _filled(q.get(field)):
                clock(q[field], field)
    for field in ('checkin', 'checkout', 'departure_date', 'service_date'):
        if _filled(q.get(field)):
            date_value(q[field], field)
    for field in sig:
        if isinstance(sig[field], (dict, list)):
            issues.append('invalid_' + field)
    if 'all_in_price' not in q:
        price = None
        issues.append('missing_all_in_price')
    else:
        price = decimal_money(q['all_in_price'], 'all_in_price')
    if q.get('price_basis') != 'all_in_total':
        issues.append('not_comparable_price_basis')
    if q.get('taxes_included') is not True or q.get('mandatory_fees_included') is not True:
        issues.append('taxes_or_mandatory_fees_unknown')
    return price, sig, issues


def compare(payload):
    require_dict(payload)
    kind = payload.get('kind', 'hotel')
    if kind not in BASE_KEYS:
        raise InputError('kind must be hotel/restaurant/transport/activity')
    options = require_list(payload.get('options'), 'options', nonempty=True)
    unique_ids(options, 'options')
    if len(options) < 2:
        raise InputError('comparison requires at least 2 options')
    results = []
    groups = {}
    for option in options:
        require_dict(option, 'option')
        q = option.get('quote')
        price, signature, issues = _read_quote(q, kind)
        signals = require_dict(option.get('signals', {}), 'signals')
        if set(signals) - set(DIMENSIONS):
            raise InputError('unsupported signals (must be shared comparison dimensions)')
        normalized = {k: bounded_number(v, 'signals.' + k) for k, v in signals.items()}
        features = require_dict(option.get('features', {}), 'features')
        entry = {
            'id': option['id'], 'name': option.get('name') or option['id'],
            'all_in_price': float(price) if price is not None else None,
            'currency': q.get('currency') if isinstance(q, dict) else None,
            'quote_normalized': not issues,
            'price_comparable': False,
            'package_equivalent': False,
            'issues': list(issues),
            'signature': signature,
            'signals': normalized,
            'features': features,
            'source': option.get('source'),
            'quote_conditions': {k: q.get(k) for k in TERM_KEYS[kind]} if isinstance(q, dict) else {},
            'evidence_status': option.get('evidence_status', 'unverified'),
            'comparison_group': None,
        }
        results.append(entry)
        if not issues:
            key = json.dumps(signature, sort_keys=True, ensure_ascii=False)
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
        comparable_groups.append({'group_id': group_id,
                                  'option_ids': [e['id'] for e in entries],
                                  'price_ranking_low_to_high': [e['id'] for e in ranked],
                                  'aligned_conditions': entries[0]['signature']})
        for entry in entries:
            entry['price_comparable'] = True
            entry['package_equivalent'] = True

    # A price order across different products is intentionally not emitted.
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

    # Pareto observation restricted to known, *listed* metrics; never a blanket
    # claim of hotel quality. Also require identical extra features so important
    # omitted attributes are not silently treated as equal.
    dominated = []
    for group in comparable_groups:
        members = [e for e in results if e['id'] in group['option_ids']]
        for a in members:
            for b in members:
                if (a is b or not a['signals'] or set(a['signals']) != set(b['signals'])
                        or a['features'] != b['features']):
                    continue
                if (b['all_in_price'] <= a['all_in_price']
                        and all(b['signals'][k] >= a['signals'][k] for k in a['signals'])
                        and (b['all_in_price'] < a['all_in_price']
                             or any(b['signals'][k] > a['signals'][k] for k in a['signals']))):
                    dominated.append({'option_id': a['id'], 'dominated_by': b['id'],
                                      'scope': 'supplied_metrics_only'})
                    break
    return {
        'task': 'compare', 'kind': kind, 'options': results,
        'comparable_option_ids': [e['id'] for e in results if e['price_comparable']],
        'comparable_groups': comparable_groups,
        'price_ranking_low_to_high': ranking,
        'dominated_options': dominated,
        'pending_normalization': [e['id'] for e in results if not e['quote_normalized']],
        'not_comparable': [e['id'] for e in results if not e['price_comparable']],
        'notes': [
            'A valid total price is not necessarily a comparable package.',
            'Price rankings are shown only within identical dated/occupancy/benefit terms.',
            'Differences in benefits, service times, transfers, baggage or refund terms must be explained as trade-offs, never silently ranked.',
            'Any numeric scores use supplied signals and do not establish real-world quality.',
            'Quote sources and availability must be checked by the host agent.',
        ],
    }
