# Design

## Positioning

Travel Advisor is a workflow-based Agent Skill intended to improve travel decision quality. It is not an independent booking platform or a route-search engine. The skill combines a host agent's existing research and communication capabilities with explicit evidence handling, quote comparability and itinerary review rules.

## Motivation

Travel planning depends on information scattered across operator notices, maps, accommodation offers, transport rules and user preferences. A page may be outdated; two similar prices may represent different products; an appealing daily schedule may be impossible in practice once transfers and buffers are counted. A coherent narrative alone does not solve these problems.

The design addresses three questions:

1. **Is the information applicable?** Check the date, venue identity, party size, fare conditions and provenance.
2. **Does the choice fit the constraints?** Separate hard requirements from preferences and explain trade-offs.
3. **Can the plan be executed?** Review time, transit, booking needs, cross-day transitions and budget; mark unresolved conditions explicitly.

## Principles

- **Task-sized assistance:** A claim check should not become an unsolicited trip plan; a local revision should preserve unaffected decisions.
- **Evidence before certainty:** Do not fill a verification gap with a fabricated live fact.
- **Comparability before ranking:** Offers with different entitlements require explicit trade-offs.
- **Staged planning and review:** Research, shortlist, compose, verify, and repair only the affected parts.
- **No separate setup:** Use the host's existing tools rather than require private APIs or user configuration.
- **Bounded complexity:** Local scripts handle deterministic checks; live research and itinerary composition remain with the host.

## Non-goals

The skill does not supply live booking inventory, a transport operator database, an offline route optimizer, automatic payments, persistent cross-session memory, or background monitoring. Actual capabilities depend on the host's available tools and permissions.
