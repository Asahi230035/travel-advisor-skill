"""Shared input checking and safe monetary, coordinate, and time helpers; stdlib only."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
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


def positive_int(value, field='count', minimum=1):
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InputError(f'{field} must be integer >= {minimum}')
    return value


def decimal_money(value, field='amount', allow_zero=True):
    if isinstance(value, (bool, list, dict)) or value is None:
        raise InputError(f'{field} must be a finite nonnegative number')
    try:
        num = Decimal(str(value))
        if not num.is_finite() or num < 0 or (not allow_zero and num == 0):
            raise InvalidOperation
        return num.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        bound = 'nonnegative' if allow_zero else 'positive'
        raise InputError(f'{field} must be a finite {bound} number')


def decimal_rate(value, field='rate'):
    if isinstance(value, (bool, list, dict)) or value is None:
        raise InputError(f'{field} must be a positive finite number')
    try:
        num = Decimal(str(value))
        if not num.is_finite() or num <= 0:
            raise InvalidOperation
        return num
    except (InvalidOperation, ValueError):
        raise InputError(f'{field} must be a positive finite number')


def bounded_number(value, field='number', lo=0, hi=100):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not lo <= value <= hi:
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
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def unique_ids(records, label='items'):
    ids = [r.get('id') for r in records]
    if any(not isinstance(v, str) or not v.strip() for v in ids) or len(set(ids)) != len(ids):
        raise InputError(f'{label} require unique nonempty string ids')


def distance_km(a, b):
    lat1, lon1 = float(a[0]), float(a[1])
    lat2, lon2 = float(b[0]), float(b[1])
    if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90 and -180 <= lon1 <= 180 and -180 <= lon2 <= 180):
        raise InputError('invalid coordinate')
    u1, u2 = math.radians(lat1), math.radians(lat2)
    dx = math.radians(lat2 - lat1)
    dy = math.radians(lon2 - lon1)
    h = math.sin(dx / 2) ** 2 + math.cos(u1) * math.cos(u2) * math.sin(dy / 2) ** 2
    return 12742 * math.asin(min(1.0, math.sqrt(h)))


def detect_lang(payload, preferred='auto'):
    if preferred in ('zh', 'en'):
        return preferred
    explicit = payload.get('lang') if isinstance(payload, dict) else None
    if explicit in ('zh', 'en'):
        return explicit
    text = str(payload)
    if re.search(r'[\u4e00-\u9fff]', text):
        return 'zh'
    return 'en'
