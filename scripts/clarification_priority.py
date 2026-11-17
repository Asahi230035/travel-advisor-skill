#!/usr/bin/env python3
"""Prioritize high-impact questions from explicit, supplied metadata; never invent answers.

The heuristics are design defaults, not validated probabilities or genuine VoI estimates.
Input: JSON with 'candidates' objects: key, question, impact(1..5),
blocking(bool), already_asked(bool), defaultable(bool), effort(1..5).
"""
import json
import sys
from pathlib import Path


def select_questions(payload):
    if not isinstance(payload.get('candidates'), list):
        raise ValueError('candidates must be a list')
    limit = payload.get('max_questions', 1)
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 3:
        raise ValueError('max_questions must be 1..3')
    available = []
    unresolved_blocker = False
    seen = set()
    for c in payload['candidates']:
        key = c['key']
        if key in seen:
            continue
        seen.add(key)
        impact = c['impact']
        effort = c.get('effort', 1)
        if not isinstance(impact, int) or not 1 <= impact <= 5:
            raise ValueError('impact must be integer 1..5')
        if not isinstance(effort, int) or not 1 <= effort <= 5:
            raise ValueError('effort must be integer 1..5')
        if c.get('blocking', False):
            unresolved_blocker = True
        if c.get('already_asked', False):
            continue
        if c.get('defaultable', False) and not c.get('blocking', False) and impact <= 2:
            continue
        priority = (100 if c.get('blocking', False) else 0) + impact * 10 - effort
        available.append((priority, key, c['question'], bool(c.get('blocking', False))))
    available.sort(key=lambda x: (-x[0], x[1]))
    selected = available[:limit]
    return {
        'questions': [{'field': key, 'question': question, 'blocking': blocking}
                      for _, key, question, blocking in selected],
        'may_proceed_provisionally': not unresolved_blocker,
        'policy': 'heuristic_question_selection_not_estimated_probability'
    }


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/clarification_priority.py examples/clarification_demo.json')
    print(json.dumps(select_questions(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))),
                     ensure_ascii=False, indent=2))
