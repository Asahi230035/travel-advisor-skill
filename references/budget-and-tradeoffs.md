# Budget balance, cost levers, and multi-person trade-offs

Load this playbook for budget breakdowns, affordability checks, option trade-offs, and multi-traveler preference coordination.

## 1. Hard constraints first (gates, never scores)
Before comparing or allocating anything, filter non-negotiable gates:
- Hard budget ceiling (if strictly fixed) and exact **budget basis** (total vs per person; includes or excludes intercity flights/trains).
- Required dates, legal/visa eligibility, mandatory accessibility/mobility/medical/dietary requirements, and already `booked`/`locked` items.
- **Unknown is not Pass**: if a required gate cannot be verified, mark it `❓` rather than silently assuming compliance.

## 2. Balanced budgeting (never over-optimize one category)
1. **Lock unavoidable fixed commitments first**: intercity rail/air, visa/insurance fees, mandatory already-booked items.
2. **Reserve contingency (~8%–12%)**: buffers dynamic rate swings, local taxis in rain, unplanned snacks/tips, or FX movement. Never spend 100% of the user's budget on paper.
3. **Protect baseline viability across all core categories**: lodging, daily meals, local transit, and activities.
4. **Tilt flexible funds moderately toward stated preferences**:
   - "We love food" means raising the food share within a bounded range while keeping lodging and transit comfortable — **never** starving lodging or putting 80% into dining.
   - Do not invent universal fixed ratios (e.g., "always 40% hotel, 30% food") — calibrate to destination price levels and trip length, and label unverified price assumptions clearly as `≈`.
5. **Present 2–3 concrete scenarios + Top 2 Levers** (see `budget` template in [task-routing-and-formats.md](task-routing-and-formats.md)):
   - Show **Tight / Balanced / Upgraded** totals AND **per-person / per-day** figures.
   - Always call out the **1–2 biggest levers** that move the budget meaningfully (e.g., shifting hotel 2 metro stops out, flying mid-week vs Friday night, mixing 1 splurge meal with local street food).
   - If the user's budget is genuinely infeasible for their stated destination/dates/expectations, say so plainly and show the specific gap plus realistic trade-offs (shorter duration, shoulder dates, alternate base area).
- When Python execution is available, `python scripts/travel.py --stdin --task budget` computes exact fixed/reserve/flexible splits, 3 scenarios, and per-person/per-day totals deterministically.

## 3. Flip conditions instead of false numeric precision
- **Avoid model-invented scores** like "Hotel A: 91.3 vs Hotel B: 89.7" when no grounded rubric exists — they create fake certainty.
- Offer **2–4 genuinely distinct candidates** (fewer is always better than padded filler options).
- Keep four dimensions visibly separate:
  1. **Feasibility gate** (`Pass` / `Fail` / `❓ Unknown`)
  2. **Preference fit & trade-offs** (qualitative, or numeric *only* when backed by explicit comparable metrics)
  3. **Evidence quality** (`✅ Verified` / `≈ Partial` / `❓ Unverified`)
  4. **Execution risk** (queues, non-refundable exposure, tight connections, weather fragility, crowd spikes)
- Always close comparisons with **Flip Conditions**: concrete "choose A if X; switch to B if Y" rules that make the decision effortless.

## 4. Multi-traveler & group fairness
- **Protect every member's non-negotiable constraints** (e.g., one person's mobility limit or food allergy applies to shared blocks unconditionally — it cannot be outvoted by three others).
- **Avoid average-score tyranny**: a plan that scores 95 for three people and 30 for one miserable member is a bad group plan. Check both group balance and lowest-member satisfaction.
- **Separate shared spend vs personal spend**: in group budgets, distinguish AA-split shared costs (shared rooms, rental car/taxis, group meals) from optional individual splurges (shopping, niche attractions, single-room supplement).
- When preferences diverge sharply, propose a **split-and-rejoin schedule** rather than forcing mediocre compromises (see [traveler-profiles-and-crossborder.md](traveler-profiles-and-crossborder.md)).
