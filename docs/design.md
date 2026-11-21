# Design (v2.0)

## Positioning

Travel Advisor is a workflow-and-craft Agent Skill designed to make AI travel advice **genuinely useful, up to date, and honest**. It is not a booking platform, an API wrapper, or an offline route optimizer. It pairs the host agent's live research capabilities with domain travel expertise, clear decision formats, and optional deterministic verification/export tools.

## Core problems solved

1. **Stale or hallucinated travel facts:** A closed museum, expired 2023 blog guide, or truncated search snippet can ruin a trip. v2.0 prohibits memory-only answers for volatile travel facts and enforces dual-date freshness, full-page verification, and visible four-state provenance (`✅ / ≈ / ⚠️ / ❓`).
2. **Misleading comparisons & hidden fees:** Headline hotel or transport prices hide city taxes, resort fees, baggage limits, non-refundable rules, and currency mismatches. v2.0 aligns terms before ranking and explains trade-offs through clear flip conditions.
3. **Unrealistic itineraries:** Generic AI plans ignore Monday museum closures, cross-city backtracking, door-to-door transit friction, arrival fatigue, senior/kid needs, and rainy-day fallbacks. v2.0 encodes practical routing, pacing, calendar-trap checks, and split-and-rejoin group mechanics.
4. **Cluttered outputs & long-conversation drift:** v2.0 defines scannable output skeletons, compact multi-turn `Trip State` snapshots, and optional `.ics` / offline HTML exports that preserve verification status.

## Design principles

- **Real-time freshness & authenticity first:** Never disguise guesses, memory, or stale posts as verified live facts.
- **Task-sized assistance:** Answer what was asked; stop at the user's boundary.
- **Progressive disclosure:** Keep `SKILL.md` lean and load domain playbooks strictly on demand.
- **Zero separate setup:** Use the host agent's native tools; keep optional helpers 100% Python stdlib-only.
- **High-leverage tooling only:** Use Python where determinism matters (money, FX, pass math, schedule audits, file exports), and let the LLM handle natural language and live research.

## Non-goals

The skill does not supply live booking inventory, private fare APIs, automated payments, offline itinerary generation, persistent cross-session storage, or background price monitoring.
