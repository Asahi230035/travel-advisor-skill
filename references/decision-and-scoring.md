# Budget balance, comparison and interpretable scoring

## Before ranking
1. Filter hard constraints first (budget ceiling if truly fixed; required travel date/activity; legal/eligibility and necessary accessibility). If a required fact cannot be established, mark `unknown` rather than `pass`.
2. Compare like with like. Hotels need matching stay dates, occupant count, room class, currency, inclusive fees, breakfast, refund conditions, membership eligibility and payment terms. A valid all-in price is not automatically an equivalent package: if benefits differ, compare qualitative trade-offs without a single cross-package price ranking. Distinguish total price from per-night price.
3. Keep provenance and data quality separate from subjective fit.

## Budget balance
Allocate fixed commitments first, then a sensible contingency and minimum viable comfort/food/local travel/activity coverage. Preferences can increase the **flexible** allocation of a category within a bounded range, while preserving other categories. The skill must never infer that “I love food” means “spend everything on food.” Do not mandate that the full budget be spent. Actual candidate bundles and time/commute costs are preferable to arbitrary universal percentages. If a user states a non-negotiable requirement, treat it as a constraint and report trade-offs or infeasibility.

## Scoring (optional)
Numerical scoring is appropriate only for grounded, comparable indicators. A suggested profile score can be `sum(weight_i * calibrated_metric_i)`, but subjective model-generated numbers without an evidence-based rubric are not trustworthy. Report separately:
- **Feasibility**: `pass`, `fail`, or `unknown` (gate).
- **Preference fit**: score or explained qualitative fit.
- **Evidence sufficiency**: verified, partial, or insufficient, with missing attributes.
- **Execution risk**: cancellations, delays, queues, mobility, overpacked days, cost volatility.

For multiple travelers, preserve each person's must-have constraints and consider both group mean satisfaction and lowest-member satisfaction. Avoid one member being repeatedly excluded by an average score. Compare rank stability when the choice changes with small weight adjustments; report a tie or trade-off rather than fake certainty.

Offer 2–4 genuinely different choices if available, not artificial variants to satisfy a quota. In a Pareto comparison, distinguish all-in price, substantive quality, refund flexibility and externalities (e.g. commute time). The offline helper accepts provided metrics; it **does not verify** their truth.

## Transport quote comparability (v1.2)

Do not treat transport offers as equivalent merely because dates, endpoints, passenger counts and headline prices match. Compare mode, departure and arrival times, transfer count, route pattern, fare class, change/refund rules and baggage allowance when applicable. Different conditions require a separate trade-off explanation; only equivalent groups should receive price rankings. Missing material terms must remain unresolved rather than silently assumed equal.
