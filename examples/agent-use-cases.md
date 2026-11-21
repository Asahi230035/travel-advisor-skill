# Real-world Agent Use Cases (Natural Language Only)

End users speak in plain language. The host agent applies `SKILL.md`, loads only the relevant `references/` playbook, runs live verification with its existing tools, and uses `scripts/travel.py` optionally for exact math or exports.

## 1. Hotel comparison with hidden fees & review screening (`compare`)
**User**: "Compare 3 hotels near Shinjuku Station for Dec 4–6 (2 adults). Prioritize quiet rooms and airport access."
- **Behavior**:
  - Live-checks current rates for Dec 4–6 (2 adults, 1 room), checking taxes, Tokyo accommodation tax, breakfast, and cancellation rules.
  - Screens recent 6–12 month reviews for noise, renovation/construction, and elevator/room-size complaints.
  - Excludes non-refundable room-only quotes from a shared price ranking with breakfast-included refundable quotes.
  - Delivers: 1-line bottom line → like-for-like table with `✅/≈/❓` badges → flip conditions → sources & retrieval date. Does **not** draft an itinerary.

## 2. Fact-checking a travel blog post (`verify`)
**User**: "This 2024 guide says the museum opens on Mondays and tickets are walk-in only. Can you verify?"
- **Behavior**:
  - Splits claims (Monday hours vs ticketing rule).
  - Queries the museum's official site (in local language for international venues) anchored to the travel year/month, opening the actual page rather than relying on a search snippet.
  - Flags stale blog content (`⚠️`) even if retrieved today; marks gated/inaccessible sites `❓`.

## 3. Transit pass break-even check (`compare` / `pass_check`)
**User**: "We're visiting Tokyo, Kyoto, and Osaka in 6 days. Is the 7-day JR Pass worth buying now?"
- **Behavior**:
  - Live-checks current JR Pass price and point-to-point Shinkansen fares (noting Nozomi/Mizuho surcharges and non-JR metro legs).
  - Computes break-even savings (optionally via `scripts/travel.py --task pass_check`), gives a direct verdict, and lists exact caveats.

## 4. Balanced budget with levers (`budget`)
**User**: "4 people, 3 days in Chengdu, total budget ¥8,000. We care about food and decent hotels."
- **Behavior**:
  - Reserves fixed transport and ~10% contingency first; tilts flexible spend moderately toward food/lodging without starving other categories.
  - Outputs Tight / Balanced ⭐ / Upgraded scenarios with per-person totals and the top 2 cost levers.

## 5. Multi-group itinerary with calendar traps & Plan B (`plan`)
**User**: "Plan a 3-day relaxed trip for 4 people (1 senior who shouldn't walk too much, 1 museum lover, 2 shoppers) from Nov 28–30."
- **Behavior**:
  - Live-checks exact weekday closures (Nov 30 is Monday!), opening hours, and door-to-door transit.
  - Clusters by neighborhood, designs a core shared anchor + 2-hour same-neighborhood split-and-rejoin window, adds 1-line rain Plan B and booking countdown, and appends the compact `Trip State` snapshot.

## 6. Local revision + optional export (`revise` + `export`)
**User**: "Swap Day 2 afternoon to a tea house, don't touch Day 3 (already booked), and export an `.ics` calendar for us."
- **Behavior**:
  - Keeps Day 3 locked items intact, checks only Day 2 adjacent transfers/hours/budget, shows a compact `Before → After` diff, and generates a clean `.ics` file marking any unverified items explicitly.
