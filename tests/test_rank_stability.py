import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from rank_stability import stability
from score_plans import DEFAULT_WEIGHTS

class StabilityTests(unittest.TestCase):
    def test_ranking_changes_when_weights_change(self):
        a = {k: 50 for k in DEFAULT_WEIGHTS}
        b = {k: 50 for k in DEFAULT_WEIGHTS}
        a['interest'] = 100
        b['comfort'] = 100
        one = dict.fromkeys(DEFAULT_WEIGHTS, 0.)
        two = dict.fromkeys(DEFAULT_WEIGHTS, 0.)
        one['interest'] = 1.
        two['comfort'] = 1.
        p = {'people': ['u'], 'plans': [
                {'id': 'A', 'validation': {'budget': 'pass'}, 'per_person': {'u': a}},
                {'id': 'B', 'validation': {'budget': 'pass'}, 'per_person': {'u': b}},
            ], 'weight_scenarios': {'interest': one, 'comfort': two}}
        result = stability(p)
        self.assertIsNone(result['robust_choice'])
        self.assertEqual(result['winner_counts']['A'], 1)
        self.assertEqual(result['winner_counts']['B'], 1)

    def test_no_feasible_plan_is_no_robust_choice(self):
        dims = {k: 80 for k in DEFAULT_WEIGHTS}
        result = stability({'people': ['u'], 'plans': [
            {'id': 'X', 'validation': {'budget': 'unknown'}, 'per_person': {'u': dims}}],
            'weight_scenarios': {'default': DEFAULT_WEIGHTS}})
        self.assertIsNone(result['robust_choice'])

if __name__ == '__main__':
    unittest.main()
