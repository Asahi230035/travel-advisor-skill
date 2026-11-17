# Evaluation guide

The unit suite validates deterministic components; it does **not** establish that an LLM follows the Skill reliably with live tools. Test both levels separately.

## Mechanical regression

```bash
python -m unittest discover -s tests -v
python scripts/travel.py --capabilities
python scripts/travel.py examples/runtime-preflight.json
python scripts/travel.py examples/runtime-verify.json
python scripts/travel.py examples/runtime-compare.json --format md
```

## Additional v1.2 review targets

Review authority classification when a neutral checked official item shares a domain with an unchecked supporting item. Review transport-offer grouping with different departure times, transfers and baggage rights. For itinerary drafts, include out-of-order stops and missing cross-day travel anchors: neither should be silently treated as feasible. These are review targets, not claims that a host-level evaluation was performed.

## Behavioral review

Use [evals/scenarios.md](../evals/scenarios.md) with at least one supported host agent. For each scenario record:
- Did the agent honor the requested scope?
- Was each clarification necessary and non-repeated?
- Did it distinguish current facts, opinions, assumptions and unknowns?
- Were quotes normalized on dates/occupancy/currency/fees/breakfast/cancellation/membership/payment? Were non-equivalent offers excluded from a shared price ranking?
- In a `plan` task, did the host actually consult appropriate current route/opening evidence and draft only the requested days, without an offline algorithm or fabricated route times?
- Did the scoring avoid unjustified numeric precision?
- Did it protect locked/booked plans and refrain from unauthorized actions?
- Did it use only supported host tools and avoid fake connectivity?

## Data-quality and safety caveat

Synthetic examples must remain labeled as synthetic. A unit test passing is not a real-time travel booking validation. Any claims about supported search sources should be verified against current host tooling; the instruction file does not grant tool access.
