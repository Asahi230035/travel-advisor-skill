# Host tools and graceful degradation

Travel Advisor Skill makes **no mandatory provider integration**. Check what search, browser, map, weather, file, calculator and execution tools the host agent *actually* offers. Use them as needed, without making the user set up API keys, environment variables, local servers, MCP clients or Python packages.

| Host capability | Work that may be completed | What must remain unclaimed |
| --- | --- | --- |
| Live booking/inventory tool | Real-time options for exact dates and party size | Access to other providers' inventories |
| Web + official sources | Source-backed rules, announcements, research | Confirmed inventory or reservations |
| Maps/routes or published timetable | Route timing for specified modes/time | Unchecked future conditions |
| Only user files / text | Offline comparisons, budgets, consistency checks | Independent verification of dynamic facts |
| No search and no data | General guidance, one key question | Live research or verified pricing |

Use normal host permission checks if applicable. Never bypass logins or content restrictions; the user may supply accessible content. Optional `scripts/travel.py` and its local modules are offline analysis utilities: no HTTP calls, API keys or provider dependencies. The `plan` mode is only a handoff to the host-agent [itinerary workflow](itinerary-planning.md) or an audit of a supplied draft; it is not an offline schedule generator. If file execution is unavailable, use the same rules through reasoning and explicitly state calculation uncertainty.
