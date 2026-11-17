# Changelog

## 1.2.0 — Evidence integrity and itinerary audit improvements

- Corrected authority checks to require directional support and verified authority on the same evidence record.
- Preserved supplied stop order, checked declared transfer origin, and added interday anchor, transport timing and source checks; unresolved data remains `unknown`.
- Expanded transport quote comparability to include mode, times, route pattern, transfers, change/refund terms and baggage.
- Clarified the host-driven planning stages and updated the relevant guidance.

## 1.1.0 — Host-driven planning and comparison integrity

- Clarified that itineraries are drafted by the host Agent with accessible search/map information; **no offline itinerary-generation algorithm** is implemented or required.
- Added `references/itinerary-planning.md` as the operational planning checklist with uncertainty/route constraints.
- Removed dedicated social-platform discovery scope and related promises.
- Corrected hotel quote comparability: all-in prices are not treated as equivalent if board, cancellation, payment terms or membership eligibility differs; only equivalent quote groups receive price rankings.
- Restricted dominance claims to supplied metrics and equal listed features; marked calculated scores as input-derived, not independent ratings.
- Added checks for empty itinerary days, missing required budget categories, and malformed session version.
- Updated bilingual README, Schema, tests, manual agent evaluations and examples.

## 1.0.0 — Initial open-source skill release

- Released `travel-advisor` as a reusable Agent Skill with optional stdlib-only validation helpers.
- Added task scoping, selective clarification, evidence rules, budget balance and local revisions.
- Added bilingual README files, GitHub CI, license, security and contribution guidance.
