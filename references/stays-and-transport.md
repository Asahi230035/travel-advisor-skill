# Stays, neighborhood selection, transport, and quote comparability

Load this playbook when helping users pick neighborhoods, compare hotels/lodging, choose between rail/air/local transit, evaluate transit passes, or align travel quotes.

## 1. Accommodation zone & hotel selection craft
- **Pick the base zone before individual hotels**: evaluate neighborhoods against the user's *actual* itinerary stops and arrival/departure hub, not generic tourist popularity.
  - *Hub radius trade-off*: staying within 5–8 minutes' walk of a multi-line transit hub saves 30–60 minutes every single day — often worth more than a slightly cheaper room requiring transfers.
  - *Airport / rail connection*: check whether direct airport express/limousine bus/rail serves the zone, especially with large luggage, kids, or early-morning flights.
  - *Micro-environment checks*: screen recent 6–12 month reviews for street/bar/rail noise, ongoing neighboring construction, elevator availability (critical in older European/Japanese buildings), room floor area (m² vs suitcase openability), and late-night street safety.
- **Minimizing hotel switches**: changing hotels inside the same city (or short 2–3 night trips) carries a hidden 2–3 hour "friction tax" (packing, checkout, luggage haul/storage, waiting for 15:00 check-in). Only recommend switching hotels when moving to a genuinely different city/region or switching trip style (e.g., city hub → hot-spring ryokan/resort).

## 2. Door-to-door transport & rail vs air decisions
Never compare flights and trains on "scheduled flight/train time" alone. Always evaluate **door-to-door total time and friction**:
- **Rail / High-speed train**: `origin → station + security/boarding buffer (20–40m) + rail ride + station → destination`. Wins heavily on city-center-to-city-center trips up to ~4–5 hours rail time, lower weather delay sensitivity, and generous luggage rules.
- **Flight**: `origin → airport + check-in/bag-drop/security (90–120m domestic, 150–180m international) + flight + deplane/immigration/baggage claim (30–60m) + airport → city`. Watch for budget-carrier hidden costs (carry-on weight/size limits, checked-bag fees, remote secondary airports).
- **Transfers & luggage**: flag multi-transfer station walks (e.g., huge interchanges without escalators) when traveling with seniors, strollers, or heavy suitcases.

## 3. Transit Pass & City Card break-even evaluation
Never recommend a rail pass, metro day-pass, or city museum pass on reputation alone — many passes lost value after price hikes!
1. **Itemize the user's actual planned legs/entries** using live-verified base fares (`✅`) or clearly labeled estimates (`≈`).
2. **Calculate true pass cost**: `pass price + mandatory seat-reservation/express surcharges + non-covered private-line/bus fares`.
3. **Check fine-print exclusions**: non-covered express trains (e.g., Nozomi/Mizuho surcharges), consecutive-day activation rules, limited reserved-seat caps, reservation lead requirements, or eligibility rules (passport/visa status).
4. **Verdict**:
   - Clear savings (e.g., >10% cheaper) → Worth buying (note activation timing).
   - Marginal (within ±5–10%) → Compare convenience/flexibility vs point-to-point IC/contactless tap.
   - Cheaper point-to-point → Recommend paying per ride / IC card and state exact savings.
- When Python execution is available, `python scripts/travel.py --stdin --task pass_check` computes exact break-even math deterministically.

## 4. Quote normalization & hidden surcharge checklist
**Never rank two quotes on headline price unless they represent an equivalent product.**

### Hotels & lodging — align before ranking
- Exact check-in / check-out dates, guest count, room count, room class/bedding, and currency.
- **All-in total** vs per-night headline rate — explicitly check for:
  - VAT / consumption tax / service charge
  - **City tax / accommodation tax / onsen bathing tax** (often collected on-site, excluded from OTA totals!)
  - **Resort fees / amenity fees / cleaning fees** (especially US hotels and vacation rentals)
- **Entitlements**: breakfast included vs room-only, free cancellation deadline vs non-refundable, pay-now vs pay-at-property, membership/loyalty gate.
- *Rule*: If Option A includes breakfast + free cancellation and Option B is non-refundable room-only, display both all-in totals clearly, **do not put them in a shared lowest-price ranking**, and explain the value trade-off explicitly.

### Transport — align before ranking
- Exact departure date, origin/destination stations or airports (secondary airports are NOT equivalent), traveler count, currency.
- Mode, departure & arrival times (flag red-eye or ultra-early departures), transfer count, route pattern (direct vs layover).
- Fare class, **checked & carry-on baggage allowance**, refund/change fees, and seat selection fees.

### Multi-currency comparison
- When comparing quotes in different currencies, convert using a **live-retrieved exchange rate** with retrieval date (`fx_as_of`), note that card FX spreads may apply, and show both original currency and converted target currency. Never use a memorized stale exchange rate.
- When Python execution is available, `python scripts/travel.py --stdin --task compare` checks quote comparability, mandatory surcharges, FX conversion, and per-night/per-person totals.
