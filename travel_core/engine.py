"""Unified deterministic offline runtime for Travel Advisor Skill v2.0."""
from __future__ import annotations

from . import budget, compare, evidence, export, planning, session
from .common import InputError, require_dict

SUPPORTED = (
    'capabilities',
    'verify',
    'compare',
    'budget',
    'pass_check',
    'plan',
    'audit',
    'revise',
    'export_ics',
    'export_html',
)


def capabilities():
    return {
        'version': '2.0.0',
        'runtime': 'Python 3.10+ standard library; entirely optional to the host agent',
        'setup_required': False,
        'api_keys_required': False,
        'environment_variables_required': False,
        'pip_dependencies': [],
        'offline': [
            'verify',
            'compare',
            'budget',
            'pass_check',
            'audit',
            'revise',
            'export_ics',
            'export_html',
        ],
        'host_agent_workflows': ['discover', 'plan'],
        'live_research': {
            'execution': 'Host agent existing native search / browser / map / weather tools',
            'freshness_policy': 'Volatile travel facts require live session verification with dual-date checks (retrieved_at + published_at) and full-page checks for operational rules.',
            'configuration': 'Zero setup. No API keys, env vars, or external packages.',
            'fallback': 'Use accessible sources or user-provided content; explicitly label unverified gaps.',
        },
        'limits': [
            'Offline CLI never performs network calls or bookings.',
            'Real-time prices, availability, closures, and schedules must be checked by the host agent.',
            'The plan task never generates itineraries offline; it only delegates to references/itinerary-and-pacing.md or audits a supplied draft.',
        ],
    }


def execute(payload, lang='auto'):
    require_dict(payload)
    task = payload.get('task')
    if task not in SUPPORTED:
        raise InputError('task must be one of: ' + ', '.join(SUPPORTED))
    if task == 'capabilities':
        return capabilities()
    if task == 'verify':
        return evidence.evaluate_claims(payload)
    if task == 'compare':
        return compare.compare(payload)
    if task == 'budget':
        required = ('total_budget', 'baseline_shares')
        if any(k not in payload for k in required):
            return {
                'task': 'budget',
                'status': 'needs_clarification_or_baseline',
                'missing': [k for k in required if k not in payload],
                'note': 'Supply trip-specific total_budget and baseline_shares; never assume universal fixed percentages.',
            }
        return budget.allocate(payload)
    if task == 'pass_check':
        return budget.pass_check(payload)
    if task == 'audit':
        return planning.audit(payload)
    if task == 'plan':
        return planning.plan(payload)
    if task == 'revise':
        revision = session.revise(payload)
        if revision['session'].get('days'):
            revision['post_edit_audit'] = planning.audit(revision['session'])
        return revision
    if task == 'export_ics':
        return export.export_ics(payload, lang=lang)
    if task == 'export_html':
        return export.export_html(payload, lang=lang)
    raise InputError('unsupported task')
