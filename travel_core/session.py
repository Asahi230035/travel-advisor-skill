"""Scoped user-owned decision state and non-destructive itinerary edits."""
from __future__ import annotations
import copy
from .common import InputError, require_dict, require_list, unique_ids

PROTECTED = {'locked', 'booked'}
STOP_MUTABLE = {'name', 'start', 'end', 'opening_window', 'opening_verified',
                'transfer_from_previous_minutes', 'transfer_source', 'reservation_required',
                'reservation_confirmed', 'latitude', 'longitude', 'notes'}


def _find_stop(state, day_date, stop_id):
    days = state.get('days', [])
    for day in days:
        if day.get('date') != day_date:
            continue
        for idx, stop in enumerate(day.get('stops', [])):
            if stop.get('id') == stop_id:
                return day, idx, stop
    raise InputError('specified day/stop not found; state left unchanged')


def revise(payload):
    require_dict(payload)
    state = require_dict(payload.get('session'), 'session')
    operations = require_list(payload.get('changes'), 'changes', nonempty=True)
    if type(state.get('version', 1)) is not int or state.get('version', 1) < 1:
        raise InputError('session.version must be positive integer')
    if 'expected_version' in payload and payload['expected_version'] != state.get('version', 1):
        raise InputError('stale session version; reload before editing')
    updated = copy.deepcopy(state)
    diffs = []
    affected = set()
    for change in operations:
        require_dict(change, 'change')
        action = change.get('op')
        when, key = change.get('date'), change.get('stop_id')
        if action not in ('replace_stop', 'update_stop', 'remove_stop', 'add_stop'):
            raise InputError('unsupported revision operation')
        if action == 'add_stop':
            day = next((d for d in updated.get('days', []) if d.get('date') == when), None)
            if day is None:
                raise InputError('day not found')
            stop = require_dict(change.get('stop'), 'change.stop')
            unique_ids(day.get('stops', []) + [stop], 'stops')
            if not stop.get('name') or not stop.get('start') or not stop.get('end'):
                raise InputError('new stop needs name/start/end')
            day['stops'].append(copy.deepcopy(stop))
            diffs.append({'action': action, 'date': when, 'new_stop': stop})
            affected.add(when)
            continue
        day, idx, original = _find_stop(updated, when, key)
        if original.get('decision_status') in PROTECTED and change.get('explicit_user_approval') is not True:
            raise InputError('locked/booked stop requires explicit user approval; no changes saved')
        if action == 'remove_stop':
            del day['stops'][idx]
            diffs.append({'action': action, 'date': when, 'old_stop': original})
        elif action == 'replace_stop':
            replacement = require_dict(change.get('stop'), 'change.stop')
            if replacement.get('id') != key:
                raise InputError('replacement must preserve stop_id')
            if replacement.get('decision_status') in PROTECTED and change.get('explicit_user_approval') is not True:
                raise InputError('cannot modify protected stop without approval')
            day['stops'][idx] = copy.deepcopy(replacement)
            diffs.append({'action': action, 'date': when, 'old_stop': original, 'new_stop': replacement})
        else:
            updates = require_dict(change.get('fields'), 'change.fields')
            if not updates or set(updates) - STOP_MUTABLE:
                raise InputError('update_stop may change only scoped stop fields')
            for field, value in updates.items():
                old = day['stops'][idx].get(field)
                day['stops'][idx][field] = copy.deepcopy(value)
                diffs.append({'action': action, 'date': when, 'stop_id': key,
                              'field': field, 'old': old, 'new': value})
        affected.add(when)
    updated['version'] = state.get('version', 1) + 1
    updated['validation_state'] = 'stale_recheck_required'
    return {'task': 'revise', 'session': updated, 'diff': diffs,
            'affected_days': sorted(affected),
            'recheck_required': ['day_timing', 'transport_links', 'budget_implications', 'opening_and_reservations'],
            'notes': 'No booking/cancellation actions were performed. Unaffected days remain unchanged.'}
