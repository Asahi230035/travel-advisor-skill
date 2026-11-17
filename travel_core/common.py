"""Shared input checking and safe monetary/time helpers; no external dependencies."""
from __future__ import annotations
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from math import isfinite
import re


class InputError(ValueError):
    """Expected, user-correctable input error."""


def require_dict(value, field='payload'):
    if not isinstance(value, dict):
        raise InputError(f'{field} must be an object')
    return value


def require_list(value, field, nonempty=False):
    if not isinstance(value, list) or (nonempty and not value):
        raise InputError(f'{field} must be {"nonempty " if nonempty else ""}array')
    return value


def decimal_money(value, field='amount'):
    if isinstance(value, (bool, list, dict)) or value is None:
        raise InputError(f'{field} must be a finite nonnegative number')
    try:
        num = Decimal(str(value))
        if not num.is_finite() or num < 0:
            raise InvalidOperation
        return num.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        raise InputError(f'{field} must be a finite nonnegative number')


def bounded_number(value, field='number', lo=0, hi=100):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or not lo <= value <= hi:
        raise InputError(f'{field} must be a finite number in [{lo}, {hi}]')
    return float(value)


def date_value(value, field='date'):
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        raise InputError(f'{field} must use YYYY-MM-DD')


def clock(value, field='time'):
    if not isinstance(value, str) or not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', value):
        raise InputError(f'{field} must use 24-hour HH:MM')
    return int(value[:2]) * 60 + int(value[3:])


def now_utc():
    return datetime.now().astimezone().astimezone(__import__('datetime').timezone.utc).isoformat(timespec='seconds')


def unique_ids(records, label='items'):
    ids = [r.get('id') for r in records]
    if any(not isinstance(v, str) or not v.strip() for v in ids) or len(set(ids)) != len(ids):
        raise InputError(f'{label} require unique nonempty string ids')
