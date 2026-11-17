import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from scope_guard import check_scope


class ScopeGuardTests(unittest.TestCase):
    def test_compare_can_do_evidence_and_scoring(self):
        self.assertTrue(check_scope({'scope':'compare','proposed_outputs':['comparison'],
                                     'proposed_operations':['research','normalize','evaluate','validate']})['within_scope'])

    def test_compare_cannot_silently_plan(self):
        r = check_scope({'scope':'compare','proposed_outputs':['itinerary'],
                         'proposed_operations':['schedule']})
        self.assertFalse(r['within_scope'])
        self.assertIn('itinerary', r['rejected']['outputs'])

    def test_verify_cannot_silently_recommend_full_trip(self):
        self.assertFalse(check_scope({'scope':'verify','proposed_outputs':['itinerary'],
                                      'proposed_operations':['research']})['within_scope'])

    def test_plan_can_include_budget_comparison(self):
        self.assertTrue(check_scope({'scope':'plan','proposed_outputs':['itinerary','budget_scenarios'],
                                     'proposed_operations':['research','budget','schedule','validate']})['within_scope'])

    def test_revise_only_returns_changes(self):
        self.assertFalse(check_scope({'scope':'revise','proposed_outputs':['itinerary'],
                                      'proposed_operations':['revise','validate']})['within_scope'])

    def test_pay_not_permitted(self):
        r = check_scope({'scope':'plan','proposed_outputs':['itinerary'],
                         'proposed_operations':['research','pay']})
        self.assertFalse(r['within_scope'])
        self.assertIn('pay', r['sensitive_operations_not_permitted'])

    def test_unknown_scope(self):
        with self.assertRaises(ValueError):
            check_scope({'scope':'other','proposed_outputs':['comparison']})

    def test_no_output(self):
        with self.assertRaises(ValueError):
            check_scope({'scope':'verify','proposed_outputs':[]})


if __name__ == '__main__':
    unittest.main()
