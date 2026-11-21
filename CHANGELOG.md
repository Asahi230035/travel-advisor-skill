# Changelog

## 2.0.0 — Real-time freshness guarantees, travel domain playbooks, decision formats & practical exporters

### Major enhancements
- **Real-time freshness & authenticity enforcement**:
  - Prohibited falling back to model training memory for volatile travel facts (prices, taxes, FX, opening hours, closures, schedules, booking windows, entry rules, venue status).
  - Upgraded `travel_core/evidence.py` with **dual-date freshness checks** (`retrieved_at` + `published_at`/`effective_date`), **future-timestamp rejection**, and a **snippet-only gate** preventing search snippets from granting authoritative support on critical operational claims.
  - Standardized four-state provenance badges (`✅ Verified`, `≈ Estimate`, `⚠️ Conflict/Stale`, `❓ Unverified`) across chat outputs and exported artifacts.
- **Reorganized progressive-disclosure knowledge base (`references/`)**:
  - Added deep domain playbooks: `itinerary-and-pacing.md`, `stays-and-transport.md`, `budget-and-tradeoffs.md`, and `traveler-profiles-and-crossborder.md`.
  - Consolidated operational rules into `task-routing-and-formats.md`, `clarification-and-state.md`, and `research-and-evidence.md` with concrete decision-ready output skeletons and compact multi-turn `Trip State` snapshots.
- **Streamlined, high-value Python toolkit (`scripts/travel.py` & `travel_core/`)**:
  - Unified all CLI operations into `scripts/travel.py` with `--stdin` piping, `--task` override, `--format json|md|ics|html`, and bilingual `--lang auto|zh|en` rendering.
  - Upgraded `compare.py` with dated multi-currency FX normalization, mandatory surcharge breakdown (city taxes, resort fees), and per-night/per-person unit figures.
  - Added `travel_core/budget.py` with 3-tier scenarios (`tight`/`balanced`/`upgraded`), per-person/per-day splits, and `pass_check` transit-pass break-even math.
  - Upgraded `travel_core/planning.py` with last-entry checks, daily pace/overload warnings, and pending reservation summaries (preserving the host-driven planning contract).
  - Added `travel_core/export.py` (pure stdlib) for RFC 5545 `.ics` calendar export and XSS-safe, mobile-friendly single-file offline HTML trip/comparison cards.
  - Retired redundant standalone glue scripts (`scope_guard.py`, `clarification_priority.py`, `rank_stability.py`, `score_plans.py`, `allocate_budget.py`) and thin modules (`clarify.py`, `places.py`).
- **Expanded evaluation & regression suite**:
  - Expanded `evals/scenarios.md` to 24 rubric-scored real-world agent evaluation scenarios.
  - Rebuilt `tests/` covering dual-date freshness, snippet gating, FX & surcharges, transit pass math, itinerary auditing, `.ics`/HTML exporting & XSS escaping, CLI piping, and zero-setup/stdlib-only repository contracts.

## 1.2.0 — Evidence integrity and itinerary audit improvements

- Corrected authority checks to require directional support and verified authority on the same evidence record.
- Preserved supplied stop order, checked declared transfer origin, and added interday anchor, transport timing and source checks; unresolved data remains `unknown`.
- Expanded transport quote comparability to include mode, times, route pattern, transfers, change/refund terms and baggage.
- Clarified the host-driven planning stages and updated the relevant guidance.

## 1.1.0 — Host-driven planning and comparison integrity

- Clarified that itineraries are drafted by the host Agent with accessible search/map information; **no offline itinerary-generation algorithm** is implemented or required.
- Corrected hotel quote comparability and dominance claims.
- Added checks for empty itinerary days, missing required budget categories, and malformed session version.

## 1.0.0 — Initial open-source skill release

- Released `travel-advisor` as a reusable Agent Skill with optional stdlib-only validation helpers.
