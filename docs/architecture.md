# Architecture (v2.0)

Travel Advisor Skill is a **host-driven workflow skill**, not a standalone booking app or offline route generator. The host AI agent owns natural-language understanding, live web/map/weather tool calls, user interaction, and itinerary composition. This repository provides progressive-disclosure domain playbooks, strict freshness/authenticity guardrails, output templates, and optional stdlib-only deterministic calculators and exporters.

```text
User request (natural language)
   │
   ▼
SKILL.md (lean router + real-time freshness rules + hard boundaries)
   │
   ├─ Core policies (on demand)
   │   ├─ references/task-routing-and-formats.md
   │   ├─ references/clarification-and-state.md
   │   └─ references/research-and-evidence.md
   │
   ├─ Domain expert playbooks (loaded only when matching the task)
   │   ├─ references/itinerary-and-pacing.md
   │   ├─ references/stays-and-transport.md
   │   ├─ references/budget-and-tradeoffs.md
   │   └─ references/traveler-profiles-and-crossborder.md
   │
   ├─ Host live tools (search / browser / maps / weather — zero setup)
   │
   └─ Optional deterministic toolkit (scripts/travel.py → travel_core/)
       ├─ verify (dual-date freshness + snippet gate + origin dedup)
       ├─ compare (quote parity + surcharges + dated FX)
       ├─ budget & pass_check (3-tier budgets + transit pass break-even)
       ├─ audit & revise (timeline/pace/interday audit + locked-item guard)
       └─ export_ics & export_html (portable offline artifacts with badges)
   │
   ▼
Decision-sized response (✅ / ≈ / ⚠️ / ❓) + compact Trip State (multi-turn)
```

## Layers

1. **Real-time authenticity & scope layer (`SKILL.md` + `research-and-evidence.md`):** bans model-memory fallbacks for volatile travel facts; enforces dual-date freshness (`retrieved_at` + `published_at`), full-page inspection over search snippets, and four-state provenance badges.
2. **Domain craft layer (`references/`):** progressive-disclosure playbooks for routing/pacing/calendar traps, stay zones & door-to-door transit, balanced budgets & flip conditions, and traveler-profile/cross-border adaptations.
3. **Deterministic calculation & export layer (`travel_core/` + `scripts/travel.py`):** optional Python 3.10+ stdlib-only engine for exact arithmetic, strict auditing, non-destructive revision, and `.ics`/HTML export. Never performs network calls or offline itinerary generation.
4. **Verification & evaluation layer (`tests/` + `evals/scenarios.md`):** automated unit/security/contract tests plus a 24-scenario behavioral evaluation rubric for live host agents.

## Runtime boundaries

- `SKILL.md`: usable immediately without Python, API keys, env vars, or external packages.
- `references/`: load only the 1–3 files relevant to the current turn.
- `scripts/travel.py`: unified optional CLI accepting JSON files or `--stdin`, outputting `json`, bilingual `md`, `ics`, or `html`.
- `plan` command: explicitly hands off to [references/itinerary-and-pacing.md](../references/itinerary-and-pacing.md) or audits a user/agent-supplied draft; **never generates itineraries offline**.
