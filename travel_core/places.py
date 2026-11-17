"""Conservative place resolution and candidate discovery from supplied records."""
from __future__ import annotations
import math
import re
import unicodedata
from .common import InputError, require_list, require_dict, unique_ids, bounded_number


def normalized_name(name):
    value = unicodedata.normalize('NFKC', str(name)).casefold()
    return re.sub(r'[\s\-\.,，。·()（）]+', '', value)


def distance_km(a, b):
    lat1, lon1 = float(a[0]), float(a[1]); lat2, lon2 = float(b[0]), float(b[1])
    # Validate before trigonometry
    if not -90 <= lat1 <= 90 or not -90 <= lat2 <= 90 or not -180 <= lon1 <= 180 or not -180 <= lon2 <= 180:
        raise InputError('invalid coordinate')
    u1, u2 = math.radians(lat1), math.radians(lat2)
    dx = math.radians(lat2-lat1); dy = math.radians(lon2-lon1)
    h = math.sin(dx/2)**2 + math.cos(u1)*math.cos(u2)*math.sin(dy/2)**2
    return 12742 * math.asin(min(1, math.sqrt(h)))


def same_place(a, b):
    # Require a shared strong identity; nearby buildings must NOT merge solely on proximity.
    if a.get('provider_id') and b.get('provider_id') and a.get('provider') == b.get('provider'):
        return a['provider_id'] == b['provider_id']
    names_a = {normalized_name(x) for x in [a.get('name', '')] + a.get('aliases', []) if x}
    names_b = {normalized_name(x) for x in [b.get('name', '')] + b.get('aliases', []) if x}
    if not names_a.intersection(names_b):
        return False
    if all(k in a and k in b for k in ('latitude', 'longitude')):
        return distance_km((a['latitude'], a['longitude']), (b['latitude'], b['longitude'])) <= 0.3
    if a.get('address') and b.get('address'):
        return normalized_name(a['address']) == normalized_name(b['address'])
    return False  # same name is not sufficient: chain restaurants etc.


def discover(payload):
    require_dict(payload)
    places = require_list(payload.get('places', []), 'places')
    unique_ids(places, 'places')
    grouped = []
    for place in places:
        require_dict(place, 'place')
        if not place.get('name'):
            raise InputError('place.name required')
        for entry in grouped:
            if same_place(entry['canonical'], place):
                entry['record_ids'].append(place['id'])
                entry['platforms'].append(place.get('provider', 'user_supplied'))
                break
        else:
            grouped.append({'canonical': place, 'record_ids': [place['id']],
                            'platforms': [place.get('provider', 'user_supplied')]})
    result = []
    for e in grouped:
        p = e['canonical']
        result.append({'id': p['id'], 'name': p['name'], 'category': p.get('category', 'unknown'),
                       'address': p.get('address'), 'location': {
                           'latitude': p.get('latitude'), 'longitude': p.get('longitude')},
                       'merged_record_ids': e['record_ids'], 'platforms': sorted(set(e['platforms'])),
                       'preference_tags': p.get('tags', []),
                       'status': 'identity_supported' if len(e['record_ids']) > 1 else 'single_source_candidate'})
    return {'task': 'discover', 'candidate_count': len(result), 'candidates': result,
            'note': 'Search results supplied by agent/user; names alone never trigger merging.'}
