# Host-driven itinerary planning

This is a **procedural guide for the host agent**. It is not a Python route optimizer and requires no standalone API integration. Use when the user asks for a complete plan or a specific day's arrangement; do not invoke for unrelated comparisons.

## 1. Confirm purpose and scope
- Decide whether the request is for a day, a multi-day itinerary, a partial section or an illustrative concept.
- Preserve explicit hard constraints: destination, exact travel dates, party size, total vs per-person budget, accessibility, required visits, existing bookings and user-locked items.
- Ask at most one decisive missing question when it blocks a usable plan (for example, destination or dates for confirmed opening hours). If the user wants inspiration or approximate planning, proceed with stated assumptions and mark it provisional.
- Do **not** make a hotel comparison into an entire trip plan.

## 2. Research and shortlist only necessary items
- Use accessible host search, map, timetable and weather tools when relevant, without asking the user to configure them.
- Choose destinations/points of interest matched to interests and season, not simply the highest online rankings. Prefer a manageable shortlist per day.
- For each essential stop, collect the identity/address, relevant opening windows, estimated visit duration, booking requirement, rough costs, sources and the date/conditions checked.
- If a route/price cannot be verified, represent it as an **unverified estimate or unknown**. Never invent specific train numbers, departure times, quotes, or route results.

## 3. Compose an itinerary using actual context
- Arrange nearby stops together. Check the user’s accommodation location and origin/destination of each day; do not assume the hotel is in a generic city center.
- Factor in door-to-door transfers (walk-to-station, waiting, changing vehicles), visit time, meal/rest breaks, entrance queues and transit buffers. Use map/timetable figures when available.
- Respect check-in/out, fixed tickets and opening windows before optimizing optional stops.
- Avoid overscheduling: the plan should have slack and a sensible pace. A scenic stop and dinner must not silently occupy the same time slot.
- Budget at the whole-trip level: non-negotiable transport, essential accommodation and meals, activities, local transit and contingency. Preferences may tilt spending but must not remove other necessities.
- For multiple days, balance different interests and strenuous days, and avoid repeated cross-city journeys.
- Record each day's actual start and end anchor (hotel, station, airport, or identified place). Where consecutive days start and end at different locations, document the interday transfer and its timing; a calendar-day boundary alone does not imply that transport exists.

## 4. Verify and repair
- Recheck hard constraints, **original** daily order, route durations, hours, reservation requirements, interday continuity and cost coverage. Do not reorder stops merely to make the schedule appear valid. Transfer estimates must refer to the intended previous stop, not a different location. If Python execution exists, the **optional** `audit` helper may check an already composed structured draft; it never produces the draft.
- A structured multi-day audit may use `days[].start_location_id`, `days[].end_location_id`, and `days[].interday_transfer` with a route's departure/arrival timestamps and verification source. If the anchors or transfer evidence are missing, the result is `unknown`, not `pass`. The optional validator checks only the supplied claims; it does not discover or verify transport.
- If critical evidence is missing, do not declare the itinerary fully feasible. State what remains tentative and what the user needs to confirm.
- Change only necessary parts to fix conflicts. Do not silently change user-locked/booked items.

## 5. Present an appropriately sized result
- Give an at-a-glance plan for the requested period: day/period, place/activity, why it fits, approximate on-site time, inter-stop transport and costs where supported.
- Clearly separate *verified facts*, *estimates* and *unknowns*. Cite official/source links for consequential time-sensitive information.
- Provide alternatives when they reflect a meaningful trade-off (budget, pace, location), not artificial variants. Explain why a choice was made and what would cause it to change.
- Finish when the user's requested planning scope is covered. Do not imply reservation or purchase.

## Failure mode and fallback
If the host cannot browse or lacks usable transit data, produce a **clearly labeled conceptual itinerary** only if that is useful to the user, without asserting specific times, live prices or availability. If the user needs confirmed real-world feasibility, state the blocker instead of pretending to have checked it.
