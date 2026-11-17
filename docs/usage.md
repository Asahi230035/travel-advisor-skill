# Usage

## Natural-language requests

Install the Skill in a supported agent's skills directory and ask a travel question normally. Hosts may trigger it automatically or allow explicit invocation. End users do not need to prepare JSON input.

### Itinerary planning

> Plan three days in Hangzhou in December for two people with a total budget of ¥3,000. Prioritize nature and avoid an exhausting pace.

The agent identifies the user's dates, budget basis and preferences, researches necessary opening and route conditions when possible, and composes a day-by-day proposal. Unverified travel times and prices remain labeled as estimates or unknowns.

### Quote comparison

> Compare these three train tickets, including departure times, transfers, baggage and refund policies, not only prices.

Check whether the offers have equivalent conditions before producing any shared price ranking. Explain materially different options as trade-offs.

### Claim verification

> This travel post says the museum is free on Mondays. Check the official rule and the applicable date.

Separate verifiable claims, cite accessed sources, and distinguish supported, contradicted, disputed and unknown findings.

### Local itinerary revision

> Replace only the afternoon on day two with a museum. Keep the morning and day three; day three's tickets are already booked.

Modify only the authorized scope and recheck affected transfers, opening windows and costs. Ask before changing locked or booked arrangements.

## Optional offline helpers

The `scripts/travel.py` command accepts structured inputs for deterministic evidence, quote, budget and itinerary review. It does not browse or book anything. Hosts without Python execution can still follow the natural-language workflow.

```bash
python scripts/travel.py --capabilities
python scripts/travel.py examples/runtime-verify.json
python scripts/travel.py examples/runtime-compare.json --format md
```

## Structured multi-day itinerary review

When an audit is requested and the host can prepare structured input, keep `days[].stops[]` in the actual visit order. `transfer_from_previous_minutes` refers to the preceding stop; `transfer_from_stop_id` can identify it explicitly. For consecutive days, `days[].end_location_id` and the following `days[].start_location_id` document the overnight location handoff.

If different locations require a transfer, `days[].interday_transfer` can record `from_location_id`, `to_location_id`, `depart_at`, `arrive_at`, `source` and `verified`. Timestamps must include an ISO 8601 UTC offset. Supplying a field is not independent evidence that a route exists or operates. Missing source, anchors or travel information should remain `unknown`.

## Outputs

Most users should receive a concise decision-oriented response: alternatives and trade-offs, relevant sources, daily itinerary where requested, approximate costs, risks and outstanding confirmations. Internal JSON fields are not required in the end-user answer.
