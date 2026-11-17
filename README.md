# Travel Advisor

An Agent Skill for researching, comparing, and planning travel with reliable sources and personalized recommendations.

[简体中文](README.zh-CN.md) · [Skill](SKILL.md) · [Examples](examples/agent-use-cases.md) · [Architecture](docs/architecture.md) · [Contributing](CONTRIBUTING.md)

## Features

- **Travel discovery** — Find destinations, attractions, restaurants, and activities based on interests and constraints.
- **Source verification** — Check travel tips and itineraries against relevant, up-to-date sources; identify conflicts and outdated claims.
- **Option comparison** — Compare hotels, transport, and activities using equivalent dates, occupancy, departure times, transfer counts, baggage, benefits, refund and payment conditions, not just headline prices or ratings.
- **Budget assistance** — Balance essential expenses, contingency, and personal priorities without overspending on one category.
- **Itinerary planning** — When asked, the agent researches locations and real transit/opening constraints, then composes a practical schedule. No local route optimizer is required.
- **Itinerary review** — Spot unrealistic connections, out-of-order stops, unverified cross-day transfers, missing reservations, budget gaps, and other constraints.
- **Personal and group preferences** — Evaluate alternatives for individuals or groups, with explainable trade-offs.
- **Focused revisions** — Change one part of a trip while keeping confirmed arrangements intact.

You can ask for a single comparison or a complete itinerary. Travel Advisor selects the relevant steps based on your request and asks follow-up questions only when essential information is missing.

## Installation

Copy this repository into your agent's skills directory. No API keys or third-party Python packages are required for the skill itself.

### Codex

```bash
git clone https://github.com/USERNAME/travel-advisor-skill.git
mkdir -p ~/.agents/skills/travel-advisor
cp -R travel-advisor-skill/. ~/.agents/skills/travel-advisor/
```

**Note:** Replace `USERNAME` with the repository owner's GitHub username when the repository is published. If you already downloaded the repository, skip `git clone`.

For project-local installation, place it in `.agents/skills/travel-advisor/` instead. Other Agent Skills-compatible hosts use their respective skill directories, such as `.claude/skills/travel-advisor/` for Claude Code.

The entry point is [`SKILL.md`](SKILL.md). After installation, ask your agent a travel-related question as usual. Hosts that support explicit invocation may also accept `$travel-advisor`.

## Usage examples

**Compare accommodations**

> Compare three hotels near Shinjuku Station for our dates. Focus on transit convenience, room size, and cancellation terms.

**Verify a travel post**

> Check whether the opening-hours claim in this travel article is accurate and current.

**Balance a budget**

> We have ¥5,000 for four people in Chengdu. Food and accommodation matter most, but keep the overall trip balanced.

**Review a plan**

> Check day two of my itinerary for unrealistic travel times. Do not change the other days.

**Plan a trip**

> Help us plan five relaxed days in Chengdu with food, local culture, and a few anime-related stops.

More examples: [Agent use cases](examples/agent-use-cases.md).

## How it works

1. **Understand the task.** Identify the requested scope, known constraints, preferences, and confirmed decisions.
2. **Clarify selectively.** Ask about missing details only when they materially affect the result.
3. **Gather evidence.** Use the host agent's available search, browsing, maps, and other tools as appropriate.
4. **Compare and validate.** Align source conditions, assess trade-offs, and check hard constraints.
5. **Present actionable results.** Explain recommendations, uncertainties, and next decisions at the level of detail requested.
6. **Update on request.** Recalculate only the affected parts when the user changes a decision.

Travel Advisor distinguishes verified facts, estimates, subjective opinions, and unknowns. Current prices and transport details depend on accessible sources and host tools. **Itinerary creation is performed by the host agent using available research**, not by an offline itinerary algorithm.

## Repository structure

```text
travel-advisor-skill/
├── SKILL.md              # Agent instructions and workflow
├── references/           # Task-specific policies
├── travel_core/          # Optional deterministic Python helpers
├── scripts/              # Optional command-line entry point
├── schemas/              # Structured data contracts
├── examples/             # Sample requests and synthetic data
├── evals/                # Agent evaluation scenarios
├── tests/                # Automated regression tests
└── docs/                 # Architecture and development notes
```

The Skill works through your agent's existing capabilities. The Python helpers are optional, use only the standard library and **do not generate itineraries or retrieve live data**. Planning follows [host-driven planning rules](references/itinerary-planning.md); runtime scripts can only check a supplied draft.

## Development

Run the automated tests:

```bash
python -m unittest discover -s tests -v
```

Inspect the available offline helper operations:

```bash
python scripts/travel.py --capabilities
python scripts/travel.py examples/runtime-compare.json --format md
```

Example inputs and outputs are synthetic test fixtures, not live prices or bookings. See [evaluation guidance](docs/evaluation.md) and [contribution guidelines](CONTRIBUTING.md).

## License

Released under the [MIT License](LICENSE). For security-related reports, see [SECURITY.md](SECURITY.md).
