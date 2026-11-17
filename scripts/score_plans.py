#!/usr/bin/env python3
"""Offline, deterministic example of preference scoring; does not verify real travel claims.

Input: a JSON file with plans, their feasibility results, per-person dimension scores,
optional person-specific weights, and evidence coverage. Scores supplied in input must
be obtained from independent, traceable calculations or a disclosed rubric.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

DIMENSIONS = (
    "interest", "budget", "time_efficiency", "comfort", "experience", "convenience", "crowd"
)
DEFAULT_WEIGHTS = {
    "interest": 0.25,
    "budget": 0.20,
    "time_efficiency": 0.15,
    "comfort": 0.15,
    "experience": 0.10,
    "convenience": 0.10,
    "crowd": 0.05,
}


def _finite_number(value, label):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{label}: expected a finite number")
    return float(value)


def _normalize_weights(weights):
    if set(weights) != set(DIMENSIONS):
        raise ValueError("weights must contain exactly the 7 scoring dimensions")
    out = {key: _finite_number(weights[key], f"weight {key}") for key in DIMENSIONS}
    if any(value < 0 for value in out.values()) or not math.isclose(sum(out.values()), 1.0, abs_tol=1e-8):
        raise ValueError("weights must be nonnegative and total 1.0")
    return out


def _score_person(dimensions, weights):
    if set(dimensions) != set(DIMENSIONS):
        raise ValueError("each person must have all 7 dimension values")
    scored = {}
    for key in DIMENSIONS:
        value = _finite_number(dimensions[key], f"dimension {key}")
        if not (0 <= value <= 100):
            raise ValueError(f"dimension {key} must be 0..100")
        scored[key] = value
    return sum(scored[key] * weights[key] for key in DIMENSIONS)


def _feasibility(validation, required_rules=()):
    if not isinstance(validation, dict) or not validation:
        return "unknown"
    allowed = {"pass", "fail", "unknown", "not_applicable"}
    if any(status not in allowed for status in validation.values()):
        raise ValueError("invalid validation status")
    if "fail" in validation.values():
        return "fail"
    if any(rule not in validation for rule in required_rules):
        return "unknown"
    if "unknown" in validation.values():
        return "unknown"
    # An all-N/A validation set does not establish feasibility.
    if "pass" not in validation.values():
        return "unknown"
    return "pass"


def evaluate(payload):
    people = payload.get("people")
    plans = payload.get("plans")
    if not isinstance(people, list) or not people or len(set(people)) != len(people):
        raise ValueError("people must be a nonempty list of unique member IDs")
    if not isinstance(plans, list) or not plans:
        raise ValueError("plans must be a nonempty list")
    default_weights = _normalize_weights(payload.get("default_weights", DEFAULT_WEIGHTS))
    per_person_weights = payload.get("person_weights", {})
    for person in per_person_weights:
        if person not in people:
            raise ValueError(f"unknown person weights: {person}")
    weights_by_person = {
        person: _normalize_weights(per_person_weights.get(person, default_weights))
        for person in people
    }
    results = []
    for plan in plans:
        plan_id = plan["id"]
        eligibility = _feasibility(
            plan.get("validation", {}), payload.get("required_validation_rules", ())
        )
        coverage = _finite_number(plan.get("evidence_coverage", 0), "evidence_coverage")
        if not 0 <= coverage <= 1:
            raise ValueError("evidence_coverage must be 0..1")
        per_person = plan.get("per_person", {})
        if set(per_person) != set(people):
            raise ValueError(f"plan {plan_id} must supply scores for all people")
        person_scores = {
            person: _score_person(per_person[person], weights_by_person[person])
            for person in people
        }
        avg = sum(person_scores.values()) / len(people)
        minimum = min(person_scores.values())
        group = 0.7 * avg + 0.3 * minimum
        results.append({
            "plan_id": plan_id,
            "eligibility": eligibility,
            "person_scores": {k: round(v, 1) for k, v in person_scores.items()},
            "mean_score": round(avg, 1),
            "minimum_member_score": round(minimum, 1),
            "group_score": round(group, 1),
            "disagreement_span": round(max(person_scores.values()) - minimum, 1),
            "evidence_coverage_percent": round(coverage * 100),
            "scoring_basis": "supplied_numeric_inputs_not_independently_verified",
            "validation": plan.get("validation", {}),
        })
    feasible = sorted((p for p in results if p["eligibility"] == "pass"), key=lambda p: p["group_score"], reverse=True)
    provisional = sorted((p for p in results if p["eligibility"] == "unknown"), key=lambda p: p["group_score"], reverse=True)
    excluded = [p for p in results if p["eligibility"] == "fail"]
    return {
        "recommended_plan_id": feasible[0]["plan_id"] if feasible else None,
        "valid_rankings": feasible,
        "provisional_pending_verification": provisional,
        "excluded_by_hard_constraints": excluded,
        "disclaimer": "Demo scores are based on user-supplied/simulated dimension ratings; no travel facts or routes have been verified by this script."
    }


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python scripts/score_plans.py examples/scoring_demo.json")
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(evaluate(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
