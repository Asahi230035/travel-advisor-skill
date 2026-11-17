#!/usr/bin/env python3
"""Sensitivity test on provided dimension scores using explicit weight scenarios.
This does not infer preferences, verify evidence, or predict user satisfaction.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
try:
    from scripts.score_plans import evaluate, _normalize_weights
except ModuleNotFoundError:  # direct execution from scripts/
    from score_plans import evaluate, _normalize_weights


def stability(payload):
    scenarios = payload.get('weight_scenarios')
    if not isinstance(scenarios, dict) or not scenarios:
        raise ValueError('weight_scenarios must be a non-empty mapping')
    base = {k: v for k, v in payload.items() if k != 'weight_scenarios'}
    outcomes = []
    counts = {}
    for name, weights in sorted(scenarios.items()):
        _normalize_weights(weights)
        scenario_input = dict(base)
        scenario_input['default_weights'] = weights
        # Omit person-level weights here to make scenario effects explicit; this
        # tool is used only when the same scenario weight vector applies to all.
        scenario_input.pop('person_weights', None)
        result = evaluate(scenario_input)
        winner = result['recommended_plan_id']
        outcomes.append({'scenario': name, 'recommended_plan_id': winner,
                         'ranked_ids': [p['plan_id'] for p in result['valid_rankings']]})
        if winner is not None:
            counts[winner] = counts.get(winner, 0) + 1
    return {'scenarios': outcomes, 'winner_counts': counts,
            'robust_choice': next(iter(counts)) if len(counts) == 1 else None,
            'note': 'Deterministic sensitivity to chosen weight scenarios only, not a statistical confidence interval.'}


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python scripts/rank_stability.py examples/ranking_scenarios.json')
    print(json.dumps(stability(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))),
                     ensure_ascii=False, indent=2))
