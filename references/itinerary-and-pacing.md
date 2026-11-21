# Host-driven itinerary planning, routing, and pacing

This is a **procedural playbook for the host agent**. It is not an offline routing engine. Use it when the user asks to plan a full trip, plan a specific day/half-day, or audit/fix an itinerary. Never generate a full itinerary unless requested.

## 1. Confirm scope and hard anchors
- Lock exact scope: full trip, single day, half-day, or conceptual outline.
- Capture non-negotiable anchors first: exact travel dates (**and day of week**), arrival/departure hubs and times, accommodation location (never assume a generic city center), party mobility/nap/dietary limits, fixed tickets, and user-locked items.
- Ask at most **one decisive question** if missing data blocks feasibility (e.g., travel dates when confirmed opening hours are needed). Otherwise proceed with declared provisional assumptions.

## 2. Live research & calendar-trap audit (before drafting)
Before placing any stop into a schedule, use the host's live tools per [research-and-evidence.md](research-and-evidence.md):
- **Confirm venue existence & current status**: verify the venue is not permanently closed, under renovation, or seasonally shut.
- **Check exact calendar traps for the travel dates**:
  - **Weekday closures**: many museums, galleries, markets, and restaurants close on Mondays/Tuesdays/Wednesdays or shift closures when a holiday falls on Monday.
  - **Local public holidays & peak windows**: national holidays (e.g., Golden Week, Obon, Lunar New Year, European bank holidays/Sunday retail closures), school breaks, major local festivals/conferences.
  - **Daylight & seasonality**: winter early sunset (e.g., 16:30 sunset breaks outdoor scenic plans), monsoon/typhoon/rainy seasons, extreme summer heat windows.
  - **Advance reservation & ticket release windows**: note exact lead times (e.g., 7/14/30/60 days ahead, release timezone/hour, official channel) and whether walk-in entry exists.
- Collect for each essential stop: verified identity/area, opening/last-entry window, realistic on-site duration, booking requirement, rough cost, source URL, and retrieval date.
- **Never invent** specific train numbers, departure times, opening hours, or transfer minutes. If route/schedule tools are unavailable, mark exact transfers `❓` and label the draft accordingly.

## 3. Spatial routing & pacing craft (how experts compose days)
- **Zone clustering & flow**: group stops within the same neighborhood or along one continuous transit corridor (loop or one-way progression). Eliminate zig-zag cross-city backtracking.
- **Anchor every day realistically**: calculate the day's start from the user's actual hotel/station/airport and end back at the real evening anchor. Respect hotel check-in (typically 14:00–15:00) and check-out (typically 10:00–12:00) plus luggage drop/pickup.
- **Door-to-door transfer realism**: transit time is never just train riding time — include walking to/from stations, ticketing/security, waiting/headway, transfers, and entrance security queues.
- **Energy & pace curve**:
  - *Arrival day / red-eye day*: keep light (1–2 nearby low-friction stops + dinner); build arrival delay buffer.
  - *Multi-day rhythm*: alternate high-walking sightseeing days with lighter neighborhood/food/rest days. Avoid stacking two heavy museums or two major hikes back-to-back.
  - *Departure day*: keep stops close to the departure hub or luggage locker; leave generous airport/station buffer.
  - *Daily capacity rule of thumb*: 2–3 substantive core stops per full day (plus meals and strolls) is comfortable for most travelers; 4+ dense ticketed stops usually triggers rush risk.
- **Meal & queue realism**: never silently schedule a scenic stop and dinner in the same slot; warn about high-queue viral restaurants and suggest off-peak timing or a nearby fallback.
- **Weather & closure resilience (Plan B)**: for every weather-sensitive outdoor block or notorious queue/sold-out venue, attach a 1-line **same-zone Plan B** (indoor alternative or nearby non-queued substitute) so bad weather doesn't force a cross-city scramble.
- **Cross-day continuity**: when consecutive days start and end in different cities or hotels, document the actual interday transfer (origin, destination, departure/arrival window, luggage handling, and verification source). A date change alone never implies valid transport.

## 4. Verify and minimally repair (before presenting)
Review the composed draft against every failure mode:
1. **Original stop order**: check stops strictly in supplied chronological order; never silently reorder to hide conflicts.
2. **Opening & last-entry windows**: confirm visit start ≥ opening AND visit start ≤ last entry AND visit end ≤ closing (accounting for the exact weekday/holiday).
3. **Transfer feasibility**: verify gap between consecutive stops ≥ door-to-door transfer time from the **actual previous stop**; missing transfer evidence stays `❓`, never treated as 0 minutes.
4. **Interday anchors**: verify overnight continuity or verified interday transport.
5. **Budget & reservation completeness**: confirm major cost categories are accounted for (not omitted) and all advance-booking items appear in the **Booking & Ticket Countdown**.
6. **Optional deterministic audit**: when Python execution is available and a complex multi-day draft benefits from mechanical verification, run `python scripts/travel.py --stdin --task audit` (the script checks supplied drafts; it **never generates** itineraries).
7. **Repair minimally**: fix conflicts by adjusting only affected optional slots; never touch `locked` or `booked` items without explicit user approval.

## 5. Present cleanly (and fall back honestly)
- Follow the `plan` skeleton in [task-routing-and-formats.md](task-routing-and-formats.md): compact overview → day-by-day table with pace label & 1-line Plan B → booking countdown sorted by earliest deadline → explicit `❓` unknowns.
- **If the host lacks live search or transit data**: either state the blocker clearly or — only if useful to the user — provide a clearly labeled **conceptual outline** without asserting live times, opening hours, or prices.
