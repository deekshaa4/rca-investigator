# INC-008: Why did the p95 latency go up on 19 March 2026?

## What changed
latency_p95_ms for region ap-south went from 137.3 to 284.2 (+107%) starting 2026-03-19T03:30:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (127 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign likely caused the sudden increase in request volume and error rate.** (traffic, confidence 90%) [E5, E2, E3]
   - Why: The flash sale campaign went live at the right time and place (127 minutes before the change).
   - Why: This led to a significant increase in request volume and error rate.
   - Why: The sudden increase in traffic overwhelmed the system, causing the p95 latency to rise.

## Ruled out
- The deployment of auth v4.9 to ap-south caused the increase in latency.: The deployment happened hours before the change, not at the right time and place. [E7]
- The deployment of catalog v1.1 to us-east caused the increase in latency.: The deployment happened hours before the change, not at the right time and place. [E7]
- The deployment of catalog v1.1 to us-east caused the scaling out in ap-south.: The deployment happened hours before the change, not at the right time and place. [E7]
- The deployment of catalog v1.1 to us-east may have caused the scaling out in ap-south.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E7, E8, E6]
- The deployment of auth v4.9 to ap-south may have caused the increase in latency.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E7, E3]

## Actions
- (corrective, high) Roll back the deployment of auth v4.9 to ap-south
- (preventive, medium) Monitor the impact of the flash sale campaign and adjust resources accordingly

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 284 ms (+107%), with a change point at 2026-03-19T03:30:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1267 per 5 min before, 4623 per 5 min after, +265%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.41% before, 0.81% after, +100%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 03:30 UTC (ap-south; 127 min before the change; record R015; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E7** (record, deploys) Deployed auth v4.9 to ap-south (auth, ap-south; 251 min before the change; record R013; fit: hours before the change, too early to explain a sudden jump)
- **E8** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E9** (record, deploys) Deployed catalog v1.1 to us-east (routine release) (catalog, us-east; 163 min before the change; record R014; fit: different service/region, so unlikely to be the cause)
