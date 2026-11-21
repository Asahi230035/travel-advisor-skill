"""Real-time freshness, authenticity, and claim-level evidence evaluation.

Never performs network calls. Evaluates evidence records gathered by the host
agent, enforcing:
1. Retrieval recency (retrieved_at vs as_of, rejecting future dates).
2. Publication/effective freshness (published_at != retrieved_at; old guides
   retrieved today stay stale).
3. Evidence depth gate (snippet-only evidence cannot grant authoritative
   support for high-impact operational claims).
4. Independent-origin deduplication and same-record authority binding.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse

from .common import InputError, date_value, require_dict, require_list

# Maximum allowed age (days) since the host actually retrieved the source.
RETRIEVAL_TTL_DAYS = {
    'price': 1,
    'availability': 1,
    'weather': 1,
    'entry_rules': 1,
    'travel_schedule': 1,
    'closure_notice': 3,
    'event': 7,
    'opening_hours': 14,
    'venue_status': 14,
}

# Maximum allowed age (days) of the source content itself (published_at / effective_date)
# for non-official or dated operational guides. Retrieving an old blog today does not make it fresh.
PUBLISHED_TTL_DAYS = {
    'price': 3,
    'availability': 1,
    'weather': 1,
    'entry_rules': 90,
    'travel_schedule': 30,
    'closure_notice': 60,
    'event': 60,
    'opening_hours': 180,
    'venue_status': 180,
}

OFFICIAL_REQUIRED = {'entry_rules'}
FULL_PAGE_REQUIRED = {'entry_rules', 'opening_hours', 'closure_notice', 'travel_schedule', 'price', 'availability'}
OFFICIAL_TYPES = {'official', 'regulator', 'operator'}
VALID_DEPTHS = {'full_page', 'official_api', 'snippet', 'summary'}


def age_days(iso_value, as_of):
    if not iso_value:
        return None
    if not isinstance(iso_value, str):
        return None
    try:
        raw = iso_value[:10]
        return (date_value(as_of) - date.fromisoformat(raw)).days
    except (ValueError, TypeError):
        return None


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


def _check_freshness(source, kind, as_of):
    """Return (is_usable, reason_code_or_none)."""
    ret_ttl = RETRIEVAL_TTL_DAYS.get(kind)
    pub_ttl = PUBLISHED_TTL_DAYS.get(kind)

    ret_age = age_days(source.get('retrieved_at'), as_of)
    if ret_age is not None and ret_age < 0:
        return False, 'future_retrieved_at'
    if ret_ttl is not None:
        if ret_age is None or ret_age > ret_ttl:
            return False, 'stale_or_missing_retrieved_at'

    # Publication / effective date check: prevents old blogs retrieved today from passing as fresh.
    pub_raw = source.get('effective_date') or source.get('published_at')
    pub_age = age_days(pub_raw, as_of)
    if pub_raw is not None and pub_age is None:
        return False, 'invalid_published_at'
    if pub_age is not None and pub_ttl is not None and pub_age > pub_ttl:
        # Official pages may have an original publication date while explicitly verified current on-page.
        is_official = source.get('source_type') in OFFICIAL_TYPES
        if not (is_official and source.get('verified_current_on_page') is True):
            return False, 'stale_published_content'
    if pub_raw is None and pub_ttl is not None:
        is_official = source.get('source_type') in OFFICIAL_TYPES
        # Non-official guides without any publication date cannot verify volatile facts.
        if not is_official and source.get('verified_current_on_page') is not True:
            return False, 'undated_non_official_source'

    return True, None


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
        stale_retrieval = []
        stale_published = []
        future_dated = []
        missing_attribution = []
        snippet_only = []

        for source in evidence:
            require_dict(source, 'evidence item')
            src_label = source.get('id') or source.get('url') or source.get('reference') or 'unknown'
            stance = source.get('stance')
            if stance not in ('support', 'contradict', 'neutral'):
                raise InputError('evidence.stance must be support/contradict/neutral')

            depth = source.get('evidence_depth', 'full_page')
            if depth not in VALID_DEPTHS:
                raise InputError('evidence.evidence_depth must be full_page/official_api/snippet/summary')

            if not source.get('url') and not source.get('reference'):
                missing_attribution.append(src_label)
                continue

            usable, reason = _check_freshness(source, kind, today)
            if not usable:
                if reason == 'future_retrieved_at':
                    future_dated.append(src_label)
                elif reason in ('stale_published_content', 'undated_non_official_source', 'invalid_published_at'):
                    stale_published.append(src_label)
                else:
                    stale_retrieval.append(src_label)
                continue

            # For high-impact operational claims, snippets cannot substantiate authoritative verdicts.
            if kind in FULL_PAGE_REQUIRED and depth in ('snippet', 'summary'):
                snippet_only.append(src_label)
                continue

            origin = source_origin(source)
            item = filtered.setdefault(origin, {
                'support': False,
                'contradict': False,
                'official_support': False,
                'official_contradict': False,
                'sources': [],
            })
            if stance != 'neutral':
                item[stance] = True
                # Authority must belong to the same checked, directional, non-snippet record.
                checked_official = (
                    source.get('source_type') in OFFICIAL_TYPES
                    and source.get('verification_status') == 'checked'
                )
                if checked_official:
                    item['official_' + stance] = True
            item['sources'].append(src_label)

        support = sum(v['support'] for v in filtered.values())
        contradict = sum(v['contradict'] for v in filtered.values())
        official_support = any(v['official_support'] and not v['contradict'] for v in filtered.values())
        official_contradict = any(v['official_contradict'] for v in filtered.values())

        if (official_contradict and official_support) or (support and contradict):
            verdict = 'contested'
            badge = '⚠️'
        elif official_contradict and not support:
            verdict = 'contradicted_by_authoritative_source'
            badge = '⚠️'
        elif kind in OFFICIAL_REQUIRED and not official_support:
            verdict = 'not_verified'
            badge = '❓'
        elif official_support:
            verdict = 'supported_by_authoritative_source'
            badge = '✅'
        elif support >= 2 and contradict == 0:
            verdict = 'corroborated_non_authoritatively'
            badge = '✅'
        elif snippet_only and not filtered:
            verdict = 'snippet_only_needs_full_page_check'
            badge = '❓'
        elif (stale_retrieval or stale_published) and not filtered:
            verdict = 'stale_needs_recheck'
            badge = '⚠️'
        else:
            verdict = 'not_verified'
            badge = '❓'

        results.append({
            'id': claim.get('id'),
            'claim': claim['text'],
            'kind': kind,
            'badge': badge,
            'verdict': verdict,
            'independent_supporting_origins': support,
            'independent_contradicting_origins': contradict,
            'stale_or_undated_sources': stale_retrieval,
            'stale_published_sources': stale_published,
            'future_dated_sources': future_dated,
            'snippet_only_sources': snippet_only,
            'sources_without_reference': missing_attribution,
            'evidence_used': sorted({ref for v in filtered.values() for ref in v['sources'] if ref}),
            'warning': (
                'Evaluates evidence records supplied by the host agent; never crawls the web. '
                'Official authority requires source_type in official/regulator/operator, '
                'verification_status=checked, fresh retrieval & content dates, and full_page/official_api depth.'
            ),
        })

    return {
        'task': 'verify',
        'as_of': today,
        'claims': results,
        'method': 'dual-date freshness + depth gate + independent-origin alignment; no offline crawling',
    }
