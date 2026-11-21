# Evaluation Guide (v2.0)

Automated unit tests validate the deterministic Python helpers and repository contracts; they do **not** establish that an LLM follows the skill reliably with live tools. Evaluate both layers separately.

## 1. Automated regression & contract tests

```bash
python3 -m unittest discover -s tests -v
```

Smoke-test the unified CLI:

```bash
python3 scripts/travel.py --capabilities
python3 scripts/travel.py examples/runtime-compare.json --format md
python3 scripts/travel.py examples/runtime-verify.json --format md
python3 scripts/travel.py examples/runtime-budget.json --format md
python3 scripts/travel.py examples/runtime-pass-check.json --format md
python3 scripts/travel.py examples/runtime-export-trip.json --format html --out /tmp/trip.html
python3 scripts/travel.py examples/runtime-export-trip.json --task export_ics --format ics --out /tmp/trip.ics
```

## 2. Live host behavioral review

Run the 24 rubric-scored prompts in [evals/scenarios.md](../evals/scenarios.md) against a real host agent (comparing baseline vs Skill enabled) and inspect:
- **Real-time freshness & authenticity**: Did the agent live-search volatile facts with current-year anchors instead of answering from memory? Did it distinguish `published_at` from `retrieved_at` and refuse to certify `✅` from truncated snippets?
- **Four-state provenance**: Were `✅ / ≈ / ⚠️ / ❓` applied honestly with real sources and dates, and preserved in any exported files?
- **Scope & clarification discipline**: Did it answer only the requested scope and ask at most one decisive question?
- **Domain craft**: Did it catch Monday/holiday closures, door-to-door transit friction, hidden surcharges/FX, transit pass break-even math, Plan B resilience, and senior/group split-and-rejoin needs?
- **Safety & ownership**: Were locked/booked items protected, prompt injections ignored, and booking/payment boundaries respected?

## Synthetic data caveat

All files in `examples/` are synthetic fixtures for testing and format demonstrations — never live travel quotes or confirmed schedules.
