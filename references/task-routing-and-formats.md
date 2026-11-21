# Task routing and decision-ready output formats

Work within the **smallest scope that completes the user's request**. Deliver only the requested mode; expand only if the user asks.

## Mode routing and stop conditions

| Mode | Trigger examples | Minimum complete deliverable | Stop condition |
| --- | --- | --- | --- |
| `discover` | "Where to stay in Kyoto?", "Good food neighborhoods in Chengdu" | 2–4 genuinely distinct options with fit reasons, pros/cons, and sources | User has a clear shortlist |
| `verify` | "Is this museum open on Mondays?", "Check if this blog post is still accurate" | Claim-by-claim table: claim, verdict (`✅/⚠️/❓`), source + dates, practical caveat | Requested claims are resolved or explicitly marked unverified |
| `compare` | "Compare these 3 hotels", "Shinkansen vs flight Tokyo–Osaka" | One-line recommendation + like-for-like table + flip conditions + sources/unknowns | User can pick with eyes open |
| `budget` | "Is ¥8,000 enough for 4 people for 3 days?", "Where will the money go?" | Fixed + reserve + flexible breakdown, 2–3 scenarios (when numeric), top 2 cost levers | Budget feasibility and trade-offs are clear |
| `plan` | "Plan a 3-day relaxed Chengdu trip", "Arrange Day 2 afternoon" | Host-researched schedule for the **requested period only**, booking timeline, Plan B, unknowns | Requested days/window are covered |
| `audit` | "Is my Day 2 too rushed?", "Check my itinerary for traps" | Issues ranked by severity (hard conflict → risk → unverified), minimal fixes | Requested scope is checked |
| `revise` | "Swap Day 2 morning, don't touch Day 3" | Compact before/after diff, affected dependencies, preserved locked items | Requested edit is applied and rechecked |
| `export` | "Export to calendar", "Make a clean page I can send to friends" | `.ics` calendar file or single-file offline HTML (via `scripts/travel.py` if available) with verification badges intact | Requested export is delivered |

Never treat a user answering one clarification question as permission to expand scope.

---

## Status badges (mandatory across all modes)

Use concise, consistent markers in the user's language:
- `✅` **Verified / 已核实**: Checked in this session via live host tools; must include source + retrieval date (and effective/published date when available). Never attach `✅` to memory-only claims.
- `≈` **Estimate / 估算**: Derived from typical ranges, user figures, or provisional assumptions; state the basis.
- `⚠️` **Conflict or Stale / 冲突或过期**: Sources contradict each other or only dated sources exist; state the discrepancy and recommend checking the official channel.
- `❓` **Unverified / 待核实**: Not checked (missing dates, no live tool, login/paywall, or live inventory unavailable); tell the user how to confirm.

---

## Standard output skeletons (practical, high-signal, zero bloat)

Adapt language to match the user; omit any column or section that adds no value for a simple query.

### 1. `compare` skeleton
1. **Bottom line (1–2 sentences)**: Best default pick and the main reason; immediately name the runner-up and when it wins.
2. **Like-for-like comparison table**:
   - Columns: Dimension | Option A | Option B | Option C (2–4 distinct options max; never pad with fillers).
   - Rows: All-in price (same dates/occupancy/currency, flag mismatched entitlements with `⚠️` and exclude from price ranking) | Location & door-to-door access | Key strengths | Notable drawbacks / recent review flags | Terms (cancellation/baggage/breakfast).
3. **Flip conditions (How to choose)**: 2–3 crisp bullet points ("Choose A if…; switch to B if…").
4. **Sources & caveats**: Retrieval date, quote basis, and what remains live-dependent (inventory, dynamic rates, FX).

### 2. `budget` skeleton
1. **Feasibility verdict (1–2 sentences)**: Feasible / tight / infeasible for the stated basis (total vs per person), plus flexible allowance left after fixed costs and reserve.
2. **Scenario table** (when a numeric budget or breakdown is requested):
   - Rows: Fixed costs | Accommodation | Food & local transit | Tickets & activities | Contingency (~10%) | **Total & Per-person**.
   - Columns: Tight (精打细算) | Balanced ⭐ (均衡推荐) | Upgraded (体验升级) | Basis & status (`✅/≈/❓`).
3. **Top 2 cost/experience levers**: The 1–2 decisions that move total spend most meaningfully (e.g., shifting hotel 2 stops out, off-peak transit timing).

### 3. `plan` skeleton (only when planning is requested)
1. **Trip overview (2–3 lines)**: Dates & weekdays, theme, base neighborhood/anchor, pace level, total estimated range (if relevant).
2. **Day-by-day compact table** (one table per requested day, showing day-of-week & pace label e.g. Light / Moderate / Full):
   - Columns: Time block | Stop / Activity | Transit & duration | Cost / Booking | Notes.
   - Directly below each day: **Plan B (rain / closure / long queue)** in 1 line for any weather-sensitive or high-queue block.
3. **Booking & ticket countdown** (sorted earliest deadline first): Lead time | Item | Official channel / closure note | Status.
4. **Unverified & user confirmations**: Clear bullet list of `❓` items (e.g., exact flight arrival time, live ticket slots).

### 4. `verify` skeleton
- Compact claim table: Claim | Verdict (`✅ Supported` / `⚠️ Contradicted or Stale` / `❓ Unverified`) | Evidence (source + published/retrieved dates) | Actionable takeaway.

### 5. `audit` & `revise` skeleton
- **`audit`**: Overall feasibility (`Pass` / `Risks found` / `Incomplete — unverified gaps`) → Issues grouped by severity (`Hard conflict` / `High risk` / `Unverified`) → Minimal repair suggestions without touching locked items.
- **`revise`**: Compact `Before → After` diff → Downstream impacts checked (adjacent transfers, opening windows, budget, reservations) → Explicit confirmation that unrelated locked/booked items stayed intact.

---

## Multi-turn `Trip State` snapshot (preventing drift)

For **single-turn quick questions**, omit this block.  
For **multi-turn planning, budgeting, or iterative revisions** (2+ turns building one trip), append a compact 3–4 line snapshot at the end so the user can audit constraints at a glance:

```markdown
> **Trip State (vN)**
> - **Locked / Booked 🔒**: [dates, confirmed flights/hotels, non-negotiable mobility/dietary limits, fixed budget ceiling]
> - **Provisional ⏳**: [current draft base area, candidate options, draft days]
> - **Open ❓**: [unresolved items that still affect execution]
```
