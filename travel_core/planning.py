"""Validate itinerary ordering, route transfers, spending and open windows.

The agent/researcher supplies verified locations and durations. This validator
never invents a train, operating hour, booking, or live road journey.
"""
from __future__ import annotations
from decimal import Decimal
from datetime import datetime, timedelta, time
from .common import InputError, require_dict, require_list, unique_ids, clock, date_value, decimal_money
from .places import distance_km


def _positive_minutes(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > 1440:
        raise InputError(f'{field} must be integer minutes 0..1440')
    return value


def _evaluate_day(day):
    date_value(day.get('date'), 'day.date')
    stops = require_list(day.get('stops', []), 'day.stops')
    unique_ids(stops, 'day.stops')
    issues = []
    checked = []
    if not stops:
        issues.append({'severity': 'unknown', 'code': 'empty_day_not_a_complete_itinerary'})
    for stop in stops:
        require_dict(stop, 'stop')
        if not stop.get('name'):
            raise InputError('stop.name required')
        st = clock(stop.get('start'), 'stop.start')
        en = clock(stop.get('end'), 'stop.end')
        if en <= st:
            issues.append({'severity': 'fail', 'code': 'invalid_stop_time', 'stop_id': stop['id']})
        opens = stop.get('opening_window')
        if opens is None:
            issues.append({'severity': 'unknown', 'code': 'opening_hours_not_checked', 'stop_id': stop['id']})
        else:
            if not isinstance(opens, dict) or 'start' not in opens or 'end' not in opens:
                raise InputError('opening_window must contain start and end')
            opening = clock(opens['start'], 'opening_window.start')
            closing = clock(opens['end'], 'opening_window.end')
            if closing <= opening:
                issues.append({'severity': 'unknown', 'code': 'special_or_overnight_hours_require_manual_check', 'stop_id': stop['id']})
            elif st < opening or en > closing:
                issues.append({'severity': 'fail', 'code': 'outside_opening_hours', 'stop_id': stop['id']})
            if stop.get('opening_verified') is not True:
                issues.append({'severity': 'unknown', 'code': 'opening_hours_unverified', 'stop_id': stop['id']})
        if stop.get('reservation_required') is True and stop.get('reservation_confirmed') is not True:
            issues.append({'severity': 'unknown', 'code': 'reservation_not_confirmed', 'stop_id': stop['id']})
        checked.append({'stop': stop, 'start': st, 'end': en})
    # Stops are an ordered route. Sorting them would invalidate the semantics
    # of transfer_from_previous_minutes and hide a malformed itinerary.
    for prev, cur in zip(checked, checked[1:]):
        if cur['start'] < prev['start']:
            issues.append({'severity': 'fail', 'code': 'stop_order_not_chronological',
                           'stop_ids': [prev['stop']['id'], cur['stop']['id']]})
            continue
        origin_id = cur['stop'].get('transfer_from_stop_id')
        if origin_id is not None and origin_id != prev['stop']['id']:
            issues.append({'severity': 'fail', 'code': 'transfer_origin_mismatch',
                           'stop_ids': [prev['stop']['id'], cur['stop']['id']],
                           'declared_from': origin_id})
        if cur['start'] < prev['end']:
            issues.append({'severity': 'fail', 'code': 'overlapping_stops',
                           'stop_ids': [prev['stop']['id'], cur['stop']['id']]})
            continue
        gap = cur['start'] - prev['end']
        supplied_transfer = cur['stop'].get('transfer_from_previous_minutes')
        if supplied_transfer is not None:
            _positive_minutes(supplied_transfer, 'transfer_from_previous_minutes')
            if gap < supplied_transfer:
                issues.append({'severity': 'fail', 'code': 'insufficient_transfer_time',
                               'stop_ids': [prev['stop']['id'], cur['stop']['id']],
                               'available_minutes': gap, 'required_minutes': supplied_transfer})
            if cur['stop'].get('transfer_source') not in ('map_route', 'operator_timetable', 'user_confirmed'):
                issues.append({'severity': 'unknown', 'code': 'transfer_duration_not_independently_verified',
                               'stop_ids': [prev['stop']['id'], cur['stop']['id']]})
        elif all(k in s['stop'] for s in (prev, cur) for k in ('latitude', 'longitude')):
            distance = distance_km((prev['stop']['latitude'], prev['stop']['longitude']),
                                   (cur['stop']['latitude'], cur['stop']['longitude']))
            issues.append({'severity': 'unknown', 'code': 'transfer_time_unknown',
                           'stop_ids': [prev['stop']['id'], cur['stop']['id']],
                           'straight_line_km': round(distance, 2)})
        else:
            issues.append({'severity': 'unknown', 'code': 'transfer_time_unknown',
                           'stop_ids': [prev['stop']['id'], cur['stop']['id']]})
    status = ('fail' if any(i['severity'] == 'fail' for i in issues)
              else 'unknown' if any(i['severity'] == 'unknown' for i in issues)
              else 'pass')
    return {'date': day['date'], 'status': status, 'issues': issues,
            'stop_count': len(stops), 'scheduled_minutes': sum(max(0, x['end']-x['start']) for x in checked)}



def _parse_boundary_datetime(value, field):
    if not isinstance(value, str):
        raise InputError(f'{field} must be ISO 8601 date-time')
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        raise InputError(f'{field} must be ISO 8601 date-time')
    if dt.tzinfo is None or dt.utcoffset() is None:
        raise InputError(f'{field} must include a timezone offset')
    return dt


def _check_interday(previous, following):
    """Check only documented interday anchors; never infer a flight from dates."""
    p_date = date_value(previous['date'])
    n_date = date_value(following['date'])
    issues = []
    if n_date <= p_date:
        issues.append({'severity': 'fail', 'code': 'days_not_chronological'})
        return {'from_date': previous['date'], 'to_date': following['date'], 'issues': issues, 'status': 'fail'}
    if n_date > p_date + timedelta(days=1):
        issues.append({'severity': 'unknown', 'code': 'unplanned_dates_between_days'})
    from_id = previous.get('end_location_id')
    to_id = following.get('start_location_id')
    same_anchors = bool(from_id and to_id and from_id == to_id)
    if same_anchors:
        if previous.get('end_location_verified') is not True or following.get('start_location_verified') is not True:
            issues.append({'severity': 'unknown', 'code': 'interday_anchor_unverified'})
    else:
        transfer = following.get('interday_transfer')
        if transfer is None:
            issues.append({'severity': 'unknown', 'code': 'interday_transfer_missing',
                           'from_location_id': from_id, 'to_location_id': to_id})
        else:
            require_dict(transfer, 'interday_transfer')
            if not from_id or not to_id:
                issues.append({'severity': 'unknown', 'code': 'interday_transfer_anchor_unidentified'})
            elif transfer.get('from_location_id') != from_id or transfer.get('to_location_id') != to_id:
                issues.append({'severity': 'fail', 'code': 'interday_transfer_anchor_mismatch'})
            departed = _parse_boundary_datetime(transfer.get('depart_at'), 'interday_transfer.depart_at')
            arrived = _parse_boundary_datetime(transfer.get('arrive_at'), 'interday_transfer.arrive_at')
            if arrived <= departed:
                issues.append({'severity': 'fail', 'code': 'invalid_interday_transfer_time'})
            if departed.date() < p_date:
                issues.append({'severity': 'fail', 'code': 'interday_departure_before_previous_day'})
            last_stops = previous.get('stops', [])
            if last_stops and departed.date() == p_date:
                last_end = datetime.combine(p_date, time.min, tzinfo=departed.tzinfo) + timedelta(
                    minutes=clock(last_stops[-1]['end'], 'previous_last_stop.end'))
                if departed < last_end:
                    issues.append({'severity': 'fail', 'code': 'interday_departure_before_last_stop_ends'})
            first_stops = following.get('stops', [])
            if first_stops:
                first_start = datetime.combine(n_date, time.min, tzinfo=arrived.tzinfo) + timedelta(
                    minutes=clock(first_stops[0]['start'], 'first_stop.start'))
                if arrived > first_start:
                    issues.append({'severity': 'fail', 'code': 'interday_arrival_after_first_stop'})
            if transfer.get('verified') is not True or transfer.get('source') not in ('map_route', 'operator_timetable', 'user_confirmed'):
                issues.append({'severity': 'unknown', 'code': 'interday_transfer_unverified'})
    status = ('fail' if any(i['severity'] == 'fail' for i in issues)
              else 'unknown' if issues else 'pass')
    return {'from_date': previous['date'], 'to_date': following['date'],
            'status': status, 'issues': issues}


def audit(payload):
    require_dict(payload)
    days = require_list(payload.get('days'), 'days', nonempty=True)
    for d in days:
        require_dict(d, 'day')
        date_value(d.get('date'), 'day.date')
    dates = [d['date'] for d in days]
    if len(dates) != len(set(dates)):
        raise InputError('day dates must be unique')
    day_results = [_evaluate_day(d) for d in days]
    boundaries = [_check_interday(a, b) for a, b in zip(days, days[1:])]
    costs = payload.get('costs', {})
    require_dict(costs, 'costs')
    confirmed = Decimal('0')
    unpriced = []
    for key, entry in costs.items():
        if not isinstance(entry, dict) or 'amount' not in entry:
            unpriced.append(key)
        else:
            confirmed += decimal_money(entry['amount'], 'costs.' + key)
    budget = payload.get('total_budget')
    money = {'itemized_total': float(confirmed), 'unpriced_categories': unpriced,
             'currency': payload.get('currency', 'CNY'), 'status': 'unknown'}
    required_categories = payload.get('required_cost_categories', [])
    require_list(required_categories, 'required_cost_categories')
    missing_categories = [k for k in required_categories if k not in costs]
    if missing_categories:
        money['missing_required_categories'] = missing_categories
    if budget is not None:
        limit = decimal_money(budget, 'total_budget')
        money['budget_limit'] = float(limit)
        if confirmed > limit:
            money['status'] = 'fail'
        elif unpriced or missing_categories or payload.get('costs_complete') is not True:
            money['status'] = 'unknown'
            money['note'] = 'Budget status stays unknown until the user/agent confirms all relevant cost categories were covered.'
        else:
            money['status'] = 'pass'
    if payload.get('currency') is None:
        money['currency_warning'] = 'Currency assumed CNY; confirm all cost entries share this currency.'
    general = [d['status'] for d in day_results] + [b['status'] for b in boundaries] + [money['status']]
    overall = ('fail' if 'fail' in general else 'unknown' if 'unknown' in general else 'pass')
    return {'task': 'audit', 'overall_status': overall, 'days': day_results,
            'interday_checks': boundaries,
            'cost_check': money, 'checks_scope': 'provided days, declared interday anchors/transfers and priced categories only',
            'limitations': ['An explicit opening window is not proof that it is current.',
                            'Missing route details stay unknown; straight-line distance is not travel time.',
                            'Interday continuity requires verified start/end anchors or a supported transfer; no live route search is performed.']}


def plan(payload):
    """Host-agent planning handoff, not a local itinerary generator.

    Planning draws on currently accessible destinations, operating schedules,
    travel routes, and user preferences. This deterministic helper only checks
    a supplied draft; it must not claim to have created an itinerary.
    """
    if not payload.get('days'):
        return {
            'task': 'plan', 'status': 'host_agent_planning_required',
            'workflow_reference': 'references/itinerary-planning.md',
            'next_step': 'Use the host agent and its available tools to research and compose the requested itinerary; never invent places, schedules or route times.',
            'automatic_offline_planning': False,
        }
    report = audit(payload)
    report['task'] = 'plan'
    report['status'] = 'provided_draft_audited'
    report['automatic_offline_planning'] = False
    return report
