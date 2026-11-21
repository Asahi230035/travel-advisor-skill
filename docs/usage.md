# Usage (v2.0)

## Natural-language workflow (end users)

Install the skill in your agent's skills directory and ask travel questions in plain language. End users never need to write JSON or run scripts.

- **Hotel / transport comparison**: *"Compare 3 hotels near Shinjuku Station for Dec 4–6 (2 adults), checking city taxes, breakfast, cancellation, and recent noise reviews."*
- **Fact-check a travel post**: *"Verify whether the opening hours and ticket rules in this blog post are still valid for November 2026."*
- **Transit pass check**: *"We're doing Tokyo–Kyoto–Osaka in 6 days. Is a 7-day JR Pass worth it?"*
- **Balanced budget**: *"4 people, 3 days in Chengdu, total budget ¥8,000. Show tight/balanced/upgraded tiers and the biggest cost levers."*
- **Itinerary planning**: *"Plan 3 relaxed days in Chengdu (Nov 28–30) for 4 people including a senior, with weekday closure checks, Plan B, and booking deadlines."*
- **Local edit & export**: *"Change Day 2 afternoon only, keep Day 3 booked tickets untouched, and export an `.ics` calendar and offline HTML sheet."*

## Optional unified CLI (agent-facing)

When Python 3.10+ execution is available, the host agent may invoke `scripts/travel.py` with either a JSON file or `--stdin`:

```bash
# Inspect zero-config offline boundaries
python3 scripts/travel.py --capabilities

# Like-for-like quote comparison (with FX & surcharges)
python3 scripts/travel.py examples/runtime-compare.json --format md

# Dual-date freshness & snippet-gate evidence audit
python3 scripts/travel.py examples/runtime-verify.json --format md

# Balanced 3-tier budget allocation
python3 scripts/travel.py examples/runtime-budget.json --format md

# Transit pass break-even math
python3 scripts/travel.py examples/runtime-pass-check.json --format md

# Export structured trip to single-file offline HTML or RFC 5545 .ics calendar
python3 scripts/travel.py examples/runtime-export-trip.json --format html --out /tmp/trip.html
python3 scripts/travel.py examples/runtime-export-trip.json --task export_ics --format ics --out /tmp/trip.ics

# Pipe JSON directly without creating temporary files
cat examples/runtime-pass-check.json | python3 scripts/travel.py --stdin --format md --lang en
```

Supported `--format` values: `json` (default), `md`, `ics`, `html`.  
Supported `--lang` values: `auto` (default), `zh`, `en`.

## Multi-day itinerary audit notes

When auditing a structured draft (`--task audit`), preserve `days[].stops[]` in chronological visit order. Provide `opening_window` (with optional `last_entry`), `opening_verified`, `transfer_from_previous_minutes`, `transfer_source`, and cross-day `end_location_id` / `start_location_id` / `interday_transfer` (with timezone-aware ISO 8601 timestamps). Missing values stay `unknown` — never assumed valid.
