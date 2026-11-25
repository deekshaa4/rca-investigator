# INC-001: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service search, region ap-south went from 0.003353 to 0.02987 (+791%) starting 2026-03-26T06:20:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (4 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **A new deployment caused the error rate to spike.** (deployment, confidence 90%) [E5]
   - Why: The deployment of search v2.20 to ap-south (E5) occurred 4 minutes before the change in error rate.
   - Why: The error rate increased sharply from 0.34% to 2.99% (E1).
   - Why: The deployment of search v2.20 to ap-south (E5) is the most recent change in the system.
   - Why: evidence_ids
2. **The deployment of search v2.20 to ap-south introduced a NullPointerException.** (unknown, confidence 80%) [E5, E7, E8]
   - Why: The deployment of search v2.20 to ap-south (E5) occurred 4 minutes before the change in error rate.
   - Why: The error rate increased sharply from 0.34% to 2.99% (E1).
   - Why: The error occurred in RequestHandler.serialize (E7 and E8).
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a sudden increase in request volume.: The request volume for service search in region ap-south stayed about the same (E3). [E3]
- The increase in error rate was due to a change in the configuration of the system.: The deployment of search v2.20 to ap-south (E5) is the most recent change in the system. [E5]
- The increase in error rate was due to a change in the behavior of an upstream service.: The deployment of catalog v6.12 to eu-west (E9) is a different service/region and occurred 4 minutes before the change in error rate. [E9]

## Actions
- (corrective, high) Roll back the deployment of search v2.20 to ap-south (R011).
- (preventive, high) Implement a robust error handling mechanism in RequestHandler.serialize (R013).
- (preventive, medium) Monitor the error rate and request volume closely for any future spikes.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.34% to 2.99% (+791%), with a change point at 2026-03-26T06:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.17).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south stayed about the same (506 per 5 min before, 603 per 5 min after, +19%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed search v2.20 to ap-south (search, ap-south; 4 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on search in ap-south (search, ap-south; 10 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 2 min after the change; record R013; fit: describes a symptom, not a change)
- **E8** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 22 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E9** (record, deploys) Deployed catalog v6.12 to eu-west (catalog, eu-west; 4 min before the change; record R012; fit: different service/region, so unlikely to be the cause)
