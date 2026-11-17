"""Evidence bookkeeping and claim-level verdicts; never substitutes for browsing."""
from __future__ import annotations
from datetime import date, datetime
from urllib.parse import urlparse
from .common import InputError, require_dict, require_list, date_value

DYNAMIC_DAYS = {'price': 1, 'availability': 1, 'opening_hours': 14,
                'event': 7, 'weather': 1, 'entry_rules': 1, 'travel_schedule': 1}
OFFICIAL_REQUIRED = {'entry_rules'}


def age_days(iso, as_of):
    if not iso:
        return None
    try:
        raw = iso[:10]
        return (date_value(as_of) - date.fromisoformat(raw)).days
    except (ValueError, TypeError):
        return None


def is_current(source, kind, as_of):
    ttl = DYNAMIC_DAYS.get(kind)
    if ttl is None:
        return True
    # For date-specific quotes, a recent retrieval alone does not assert same dates/rates:
    # this is a recency gate, not a truth guarantee.
    age = age_days(source.get('retrieved_at'), as_of)
    return age is not None and 0 <= age <= ttl


def source_origin(source):
    origin = source.get('independent_origin')
    if origin:
        return str(origin).strip().lower()
    url = source.get('url') or ''
    if url:
        host = urlparse(url).hostname
        if host:
            return host.removeprefix('www.').lower()
    return 'unattributed:' + str(source.get('id', 'unknown'))


def evaluate_claims(payload):
    require_dict(payload)
    claims = require_list(payload.get('claims'), 'claims', nonempty=True)
    today = payload.get('as_of') or date.today().isoformat()
    date_value(today, 'as_of')
    results = []
    for claim in claims:
        require_dict(claim, 'claim')
        if not claim.get('text'):
            raise InputError('claim.text is required')
        kind = claim.get('kind', 'general')
        evidence = require_list(claim.get('evidence', []), 'claim.evidence')
        filtered = {}
        old, missing_attribution = [], []
        for source in evidence:
            require_dict(source, 'evidence item')
            stance = source.get('stance')
            if stance not in ('support', 'contradict', 'neutral'):
                raise InputError('evidence.stance must be support/contradict/neutral')
            if not source.get('url') and not source.get('reference'):
                missing_attribution.append(source.get('id', 'unknown'))
                continue
            if not is_current(source, kind, today):
                old.append(source.get('id', 'unknown'))
                continue
            origin = source_origin(source)
            # An origin may produce multiple different pages but only one vote.
            # Contradictory statements from a single origin stay disputed.
            item = filtered.setdefault(origin, {'support': False, 'contradict': False,
                                                'official_support': False, 'official_contradict': False,
                                                'sources': []})
            if stance != 'neutral':
                item[stance] = True
                # Authority is an attribute of the *same* checked, directional
                # evidence item. A neutral official page must not upgrade an
                # unrelated supporting page on the same domain.
                checked_official = (source.get('source_type') in ('official', 'regulator', 'operator')
                                    and source.get('verification_status') == 'checked')
                if checked_official:
                    item['official_' + stance] = True
            item['sources'].append(source.get('id') or source.get('url') or source.get('reference'))
        support = sum(v['support'] for v in filtered.values())
        contradict = sum(v['contradict'] for v in filtered.values())
        official_support = any(v['official_support'] and not v['contradict'] for v in filtered.values())
        official_contradict = any(v['official_contradict'] for v in filtered.values())
        if official_contradict and official_support or (support and contradict):
            verdict = 'contested'
        elif official_contradict and not support:
            verdict = 'contradicted_by_authoritative_source'
        elif kind in OFFICIAL_REQUIRED and not official_support:
            verdict = 'not_verified'
        elif official_support:
            verdict = 'supported_by_authoritative_source'
        elif support >= 2 and contradict == 0:
            verdict = 'corroborated_non_authoritatively'
        else:
            verdict = 'not_verified'
        results.append({'id': claim.get('id'), 'claim': claim['text'], 'kind': kind,
                        'verdict': verdict, 'independent_supporting_origins': support,
                        'independent_contradicting_origins': contradict,
                        'stale_or_undated_sources': old,
                        'sources_without_reference': missing_attribution,
                        'evidence_used': sorted({ref for v in filtered.values() for ref in v['sources'] if ref}),
                        'warning': 'This evaluates evidence records supplied by an agent/person, not direct webpage verification. Official authority requires source_type and verification_status=checked.'})
    return {'task': 'verify', 'as_of': today, 'claims': results,
            'method': 'source-alignment-and-claim-verdict; no automated crawling'}
