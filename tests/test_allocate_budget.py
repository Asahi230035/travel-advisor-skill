import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from allocate_budget import allocate


class AllocationTests(unittest.TestCase):
    def setUp(self):
        self.base = {
            "total_budget": 3000,
            "fixed_costs": {"train": 600},
            "reserve_amount": 300,
            "baseline_shares": {"lodging": 0.4, "food": 0.3, "activities": 0.2, "local_transport": 0.1},
            "minimum_shares": {"lodging": 0.2, "food": 0.18, "activities": 0.1, "local_transport": 0.06}
        }

    def test_balanced_when_unspecified(self):
        result = allocate(self.base)
        self.assertEqual(result["preference_adjusted"], result["balanced_baseline"])
        self.assertEqual(result["sum_check"], 3000)

    def test_lodging_preference_moderate_with_limits(self):
        result = allocate({**self.base, "priorities": {"lodging": "moderate"}})
        self.assertGreater(result["preference_adjusted"]["lodging"], result["balanced_baseline"]["lodging"])
        self.assertLessEqual(result["preference_adjusted"]["lodging"] - result["balanced_baseline"]["lodging"], 2100 * 0.08 + 0.01)
        self.assertGreaterEqual(result["preference_adjusted"]["food"], 2100 * .18)
        self.assertEqual(result["sum_check"], 3000)

    def test_multiple_priorities(self):
        res = allocate({**self.base, "priorities": {"lodging": "slight", "food": "moderate"}})
        self.assertGreater(res["preference_adjusted"]["food"], res["balanced_baseline"]["food"])
        self.assertEqual(res["sum_check"], 3000)

    def test_fixed_costs_cannot_consume_reserve(self):
        with self.assertRaises(ValueError):
            allocate({**self.base, "fixed_costs": {"train": 2900}})

    def test_reject_impossible_minimum(self):
        with self.assertRaises(ValueError):
            allocate({**self.base, "minimum_shares": {"lodging": 0.6}})

    def test_unknown_priority_rejected(self):
        with self.assertRaises(ValueError):
            allocate({**self.base, "priorities": {"shoes": "moderate"}})

    def test_explicit_priority_still_retains_floor(self):
        res = allocate({**self.base, "priorities": {"lodging": "explicit"}})
        self.assertGreaterEqual(res["preference_adjusted"]["food"], 2100*.18)
        self.assertEqual(res["sum_check"], 3000)


if __name__ == "__main__":
    unittest.main()
