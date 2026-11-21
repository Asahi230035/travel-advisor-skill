# Travel Advisor

An evidence-first, real-time travel planning and decision Agent Skill — combining domain travel craft, strict freshness/authenticity verification, decision-ready output formats, and optional zero-setup Python utilities.

[简体中文](README.zh-CN.md) · [Skill Entry](SKILL.md) · [Use Cases](examples/agent-use-cases.md) · [Architecture](docs/architecture.md) · [Changelog](CHANGELOG.md)

## What makes v2.0 different

- **Real-time freshness & authenticity first** — Never falls back to model memory for prices, taxes, exchange rates, opening hours, closures, timetables, or entry rules. Enforces temporal anchoring, local-language primary-source checks, full-page verification over search snippets, and `published_at` vs `retrieved_at` separation.
- **Visible four-state provenance (`✅ / ≈ / ⚠️ / ❓`)** — Every consequential figure or operational claim shows whether it was live-verified in the current session, estimated, conflicting/stale, or still unverified — both in chat and in exported files.
- **Genuine travel planning craft (progressive disclosure)** — Specialized domain playbooks loaded only on demand:
  - *Itinerary & pacing*: neighborhood clustering, arrival/departure buffers, energy curves, weekday-closure & holiday trap checks, booking countdowns, and 1-line rain/queue Plan B.
  - *Stays & transport*: hub-radius selection, hotel-switching friction, door-to-door rail vs air accounting, transit pass break-even math, recent negative-review screening, and hidden surcharge checks (city taxes, resort fees, baggage).
  - *Budgets & trade-offs*: fixed + reserve + 3-tier flexible scenarios (`Tight / Balanced / Upgraded`), top-2 cost levers, flip conditions instead of false numeric scores, and group fairness.
  - *Traveler profiles & cross-border*: kids, seniors/mobility, small-group split-and-rejoin windows, solo travel, and official visa/passport/payment/connectivity checks.
- **Practical, uncluttered outputs & optional exports** — Scannable tables, multi-turn `Trip State` snapshots to prevent constraint drift, plus optional offline export to `.ics` calendars and mobile-friendly single-file HTML cards.
- **Strict scope & user ownership** — Answers only what was asked, asks at most one high-impact question when needed, and protects `locked`/`booked` arrangements during local edits.

## Installation

Copy this repository into your agent's skills directory. **No API keys, environment variables, or third-party Python packages are required.**

### Codex / Antigravity / Agent Skills hosts

```bash
git clone https://github.com/Asahi230035/travel-advisor-skill.git
mkdir -p ~/.agents/skills/travel-advisor
cp -R travel-advisor-skill/. ~/.agents/skills/travel-advisor/
```

For workspace-local installation, place it in `.agents/skills/travel-advisor/`. Other compatible hosts use their own skill folder (e.g., `.claude/skills/travel-advisor/` for Claude Code).

The entry point is [`SKILL.md`](SKILL.md). Ask travel questions in natural language as usual.

## Usage examples

- **Compare hotels**: *"Compare 3 hotels near Shinjuku Station for Dec 4–6 (2 adults). Prioritize quiet rooms and airport access."*
- **Verify claims**: *"Check whether this travel guide's opening hours and Monday schedule are still accurate."*
- **Transit pass math**: *"We're visiting Tokyo, Kyoto, and Osaka in 6 days — is a 7-day JR Pass worth buying now?"*
- **Balance a budget**: *"4 people, 3 days in Chengdu, total budget ¥8,000. Food and decent lodging matter most."*
- **Audit / revise locally**: *"Check if Day 2 is too rushed and swap the afternoon to a tea house. Don't touch Day 3 (already booked)."*
- **Plan & export**: *"Plan a 3-day relaxed trip for 4 people including a senior, then export an `.ics` calendar and an offline HTML sheet."*

See [examples/agent-use-cases.md](examples/agent-use-cases.md) for detailed walkthroughs.

## Repository structure

```text
travel-advisor-skill/
├── SKILL.md                 # Lean entry point, real-time freshness rules & routing map
├── references/              # On-demand core policies & domain expert playbooks (7 files)
├── travel_core/             # Optional stdlib-only deterministic calculators, auditor & exporters
├── scripts/travel.py        # Unified optional CLI (--stdin, --format json|md|ics|html, --lang)
├── schemas/                 # Illustrative JSON contracts
├── examples/                # Synthetic demos & natural-language walkthroughs
├── evals/scenarios.md       # 24-scenario agent behavioral evaluation suite with rubrics
├── tests/                   # Automated unit, security & repo-contract tests
└── docs/                    # Architecture, design, usage & evaluation docs
```

**Important boundary:** Live research and itinerary composition are always performed by the host agent using its accessible tools. The optional Python CLI never accesses the network, never books anything, and **never generates itineraries offline**.

## Optional CLI & testing

Run the full automated test suite:

```bash
python3 -m unittest discover -s tests -v
```

Try the unified offline CLI (synthetic fixtures only):

```bash
python3 scripts/travel.py --capabilities
python3 scripts/travel.py examples/runtime-compare.json --format md
python3 scripts/travel.py examples/runtime-verify.json --format md
python3 scripts/travel.py examples/runtime-budget.json --format md
python3 scripts/travel.py examples/runtime-pass-check.json --format md
python3 scripts/travel.py examples/runtime-export-trip.json --format html --out /tmp/trip.html
python3 scripts/travel.py examples/runtime-export-trip.json --task export_ics --format ics --out /tmp/trip.ics
```

See [docs/evaluation.md](docs/evaluation.md) and [docs/usage.md](docs/usage.md).

## License

Released under the [MIT License](LICENSE). Security disclosures: [SECURITY.md](SECURITY.md).
