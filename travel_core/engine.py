"""One coherent runtime for partial and complete travel tasks."""
from __future__ import annotations
from .common import InputError, require_dict
from . import clarify, evidence, places, compare, planning, session

SUPPORTED = ('preflight', 'discover', 'verify', 'compare', 'budget', 'plan', 'audit',
             'revise', 'score', 'rank_stability', 'scope', 'capabilities')


def capabilities():
    return {
        'runtime': 'Python 3 standard library; entirely optional to the host agent',
        'setup_required': False,
        'api_keys_required': False,
        'environment_variables_required': False,
        'pip_dependencies': [],
        'offline': ['preflight', 'discover', 'verify', 'compare', 'budget',
                    'audit', 'revise', 'score', 'rank_stability', 'scope'],
        'host_agent_workflows': ['plan'],
        'live_research': {
            'execution': 'Host agent existing native search / web / map / weather tools',
            'configuration': 'No user setup. The agent automatically uses tools available in the current host.',
            'fallback': 'Use accessible sources or user-provided content; explicitly mark missing verification.',
            'unavailable': 'No live inventory, private third-party content, booking or payments are guaranteed.'
        },
        'limits': [
            'Offline CLI never performs network calls.',
            'Real-time availability and price verification depend on already available host tools.',
            'Natural-language interpretation and browsing are performed by the host agent.',
            'The plan task delegates itinerary creation to the host agent; no offline planner is implemented.',
        ],
    }


def execute(payload):
    require_dict(payload)
    task = payload.get('task')
    if task not in SUPPORTED:
        raise InputError('task must be one of: ' + ', '.join(SUPPORTED))
    if task == 'capabilities':
        return capabilities()
    if task == 'preflight':
        data = dict(payload)
        data['task'] = payload.get('target_task', 'discover')
        return clarify.preflight(data)
    if task == 'score':
        from scripts.score_plans import evaluate
        return {'task': 'score', **evaluate(payload)}
    if task == 'rank_stability':
        from scripts.rank_stability import stability
        return {'task': 'rank_stability', **stability(payload)}
    if task == 'scope':
        from scripts.scope_guard import check_scope
        return {'task': 'scope', **check_scope(payload)}
    if task == 'budget':
        required = ('total_budget', 'baseline_shares')
        if any(k not in payload for k in required):
            return {'task': 'budget', 'status': 'needs_clarification_or_baseline',
                    'missing': [k for k in required if k not in payload],
                    'note': 'Never synthesize a budget or baseline distribution without explaining assumptions.'}
        from scripts.allocate_budget import allocate
        return {'task': 'budget', **allocate(payload)}
    if task == 'revise':
        revision = session.revise(payload)
        if revision['session'].get('days'):
            revision['post_edit_audit'] = planning.audit(revision['session'])
        return revision
    check = clarify.preflight(payload)
    if not check['may_proceed']:
        return {'task': task, 'status': 'needs_clarification', 'question': check['ask_next'],
                'unresolved': check['unresolved']}
    if task == 'verify':
        return evidence.evaluate_claims(payload)
    if task == 'discover':
        return places.discover(payload)
    if task == 'compare':
        return compare.compare(payload)
    if task == 'audit':
        return planning.audit(payload)
    if task == 'plan':
        return planning.plan(payload)
    raise InputError('unsupported task')
