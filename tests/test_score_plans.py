import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from score_plans import DEFAULT_WEIGHTS, _feasibility, _normalize_weights, evaluate


class ScoreTests(unittest.TestCase):
    def setUp(self):
        self.base_dim = {key: 80 for key in DEFAULT_WEIGHTS}

    def _plan(self, name, state="pass", persons=None):
        persons = persons or {"a": self.base_dim, "b": self.base_dim}
        return {
            "id": name, "validation": {"hard_budget": state},
            "evidence_coverage": 0.6, "per_person": persons
        }

    def test_default_weights_sum_to_one(self):
        self.assertAlmostEqual(sum(_normalize_weights(DEFAULT_WEIGHTS).values()), 1)

    def test_failing_plan_not_recommended(self):
        inp = {
            "people": ["a", "b"],
            "plans": [self._plan("A", "fail"), self._plan("B", "pass")]
        }
        result = evaluate(inp)
        self.assertEqual(result["recommended_plan_id"], "B")
        self.assertEqual(result["excluded_by_hard_constraints"][0]["plan_id"], "A")

    def test_unknown_is_provisional_even_if_higher(self):
        all_100 = {key: 100 for key in DEFAULT_WEIGHTS}
        inp = {
            "people": ["a", "b"],
            "plans": [
                self._plan("A", "unknown", {"a": all_100, "b": all_100}),
                self._plan("B", "pass")
            ]
        }
        result = evaluate(inp)
        self.assertEqual(result["recommended_plan_id"], "B")
        self.assertEqual(result["provisional_pending_verification"][0]["plan_id"], "A")

    def test_fairness_penalizes_lower_minimum(self):
        high = {key: 100 for key in DEFAULT_WEIGHTS}
        low = {key: 0 for key in DEFAULT_WEIGHTS}
        fair = {key: 60 for key in DEFAULT_WEIGHTS}
        result = evaluate({
            "people": ["a", "b"],
            "plans": [
                self._plan("unequal", persons={"a": high, "b": low}),
                self._plan("equal", persons={"a": fair, "b": fair})
            ]
        })
        self.assertEqual(result["recommended_plan_id"], "equal")
        self.assertEqual(result["valid_rankings"][0]["group_score"], 60)

    def test_invalid_weights_rejected(self):
        invalid = dict(DEFAULT_WEIGHTS)
        invalid["interest"] = 0.9
        with self.assertRaises(ValueError):
            _normalize_weights(invalid)

    def test_absent_feasibility_is_unknown(self):
        self.assertEqual(_feasibility({}), "unknown")

    def test_all_not_applicable_is_not_pass(self):
        self.assertEqual(_feasibility({"optional": "not_applicable"}), "unknown")

    def test_required_validation_missing_is_unknown(self):
        self.assertEqual(_feasibility({"hard_budget": "pass"}, ["opening_hours"]), "unknown")

    def test_dimension_range_checked(self):
        bad = dict(self.base_dim)
        bad["budget"] = 103
        with self.assertRaises(ValueError):
            evaluate({"people": ["a", "b"], "plans": [self._plan("bad", persons={"a": bad, "b": bad})]})


if __name__ == "__main__":
    unittest.main()
