# Architecture

Travel Advisor Skill is a **workflow skill**, not a standalone app or service. The host AI agent owns language comprehension, browser/tool calls, user interaction, and (if supported) user-authorized state. The repo adds policy and deterministic helpers.

```text
User request
   │
   ▼
SKILL.md → scope router → selective clarification
   │
   ├─ host search/browsing/maps/weather (if available)
   │           └─ source records / normalized options
   ├─ references/evidence-policy.md
   ├─ references/decision-and-scoring.md
   ├─ optional travel_core (offline deterministic checks)
   └─ references/state-and-revision.md
   │
   ▼
Decision-sized answer + explicit evidence/unknowns
```

## Layers

1. **Interaction/guardrails:** smallest sufficient task, never unnecessary full itinerary; one high-impact question when needed.
2. **Evidence:** fact claims and their origin, provenance and freshness; subjective experience separate from operational facts.
3. **Decision support:** normalized quotes, balanced budgeting, individual/group scoring, caveats.
4. **Planning & feasibility:** only the host agent composes an itinerary using accessible research, following [the workflow](../references/itinerary-planning.md). Optional scripts can check a supplied draft; unknown is not pass.
5. **State:** user decisions vs provisional assumptions; local edits and re-check of affected items.

## Runtime boundaries

- `SKILL.md`: directly usable without Python, API keys or setup.
- `references/`: load the minimum relevant policy at runtime.
- `travel_core/` + `scripts/`: offline Python 3.10+ helpers on user/agent-provided JSON; **no live browsing**.
- `schemas/`: illustrative contracts; agent need not ask end users to write JSON.
- `examples/`: **synthetic** tests and demonstrations.

## Trade-offs and non-goals

Travel Advisor Skill intentionally delegates connectivity to the host; this simplifies installation but limits consistent coverage across agents. Travel providers' private rate/availability feeds, automated purchases, alerts and persistent preference stores are not included. The agent must not pretend otherwise. A quoted score is never a substitute for independently verified facts.

## v1.2 decision checks

- `travel_core/evidence.py` tracks authoritative support at the individual checked evidence-item level, not by combining attributes from separate records that share an origin. Its outputs still depend on externally supplied source labels.
- `travel_core/compare.py` adds transport timing, route/transfer, change/refund and baggage conditions to comparisons. Offers with materially different conditions must be evaluated separately.
- `travel_core/planning.py` checks stop order as supplied and declared transfer origins, plus explicitly provided interday anchors and transfers. Missing information is not proof of feasibility.
- The host agent remains responsible for researching and composing actual itineraries. Offline scripts can inspect structured drafts but cannot fetch routes or verify live services.
