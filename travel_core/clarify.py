"""Task-driven, small-question preflight; never insists on full itinerary metadata."""
from __future__ import annotations
from .common import InputError, require_dict

QUESTIONS = {
    'destination': '想研究哪个目的地或区域？',
    'checkin': '酒店的入住与退房日期分别是什么？',
    'party': '需要按几个人、几间房比较？',
    'budget': '预算上限是多少？是总预算还是人均预算？',
    'date': '具体出行日期是什么？这样才能核实实时价格、营业及活动信息。',
    'claim': '请提供需要核验的具体内容、链接或截图。',
    'items': '请提供至少两个要比较的具体选项，或告诉我希望在哪个区域搜索。',
    'existing_plan': '请提供需要审查或修改的行程内容。',
    'change': '希望修改哪一天、哪个项目，以及什么内容？',
}


def preflight(payload):
    require_dict(payload)
    task = payload.get('task')
    if task not in ('discover', 'verify', 'compare', 'budget', 'plan', 'audit', 'revise'):
        raise InputError('unknown task')
    context = require_dict(payload.get('context', {}), 'context')
    kind = payload.get('kind') or context.get('kind')
    gaps = []
    def add(field, blocking, why):
        if field not in context.get('answered_or_declined', []):
            gaps.append({'field': field, 'blocking': blocking, 'why': why, 'question': QUESTIONS[field]})
    if task == 'verify' and not payload.get('claims'):
        add('claim', True, 'No claim was provided.')
    if task == 'compare':
        if len(payload.get('options', [])) < 2 and not context.get('search_requested'):
            add('items', True, 'Need at least two candidates for a direct comparison.')
        if kind == 'hotel' and context.get('live_price_required', False):
            if not context.get('checkin') or not context.get('checkout'):
                add('checkin', True, 'Hotel quotes change by stay dates.')
            if not context.get('guests') or not context.get('rooms'):
                add('party', True, 'Occupancy affects the price.')
    if task == 'budget' and context.get('total_budget') is None and not payload.get('total_budget'):
        add('budget', True, 'A fixed budget allocation requires a total envelope.')
    if task == 'plan' and not payload.get('days') and not context.get('destination') and not payload.get('destination'):
        add('destination', True, 'A specific itinerary needs a travel location.')
    if task == 'plan' and context.get('live_schedule_required', False) and not context.get('start_date'):
        add('date', True, 'Real-time availability requires travel dates.')
    if task == 'audit' and not payload.get('days'):
        add('existing_plan', True, 'No itinerary to audit.')
    if task == 'revise' and not payload.get('changes'):
        add('change', True, 'No requested change was supplied.')
    # A nonessential preference question is never mandatory. Agent may infer balanced default.
    urgent = sorted(gaps, key=lambda x: not x['blocking'])
    return {'task': task, 'may_proceed': not any(g['blocking'] for g in gaps),
            'ask_next': urgent[0] if urgent else None, 'unresolved': urgent,
            'policy': 'One high-impact question at a time, otherwise use declared assumptions.'}
