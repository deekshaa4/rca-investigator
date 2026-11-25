# INC-021: Why did the error rate go up on 07 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.004141 to 0.03964 (+857%) starting 2026-03-07T08:20:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of catalog v2.23 caused the error rate to spike.** (deployment, confidence 90%) [E5, E8, E9]
   - Why: The deployment of catalog v2.23 introduced a new version of the RequestHandler that had a NullPointerException.
   - Why: This NullPointerException led to a high error rate in the service catalog.
   - Why: The error rate increased from 0.41% to 3.96% in the region us-east.
   - Why: evidence_ids_supporting_chain

## Ruled out
- The error rate spike is due to a sudden increase in request volume.: The request volume for the service catalog in region us-east did not change significantly. [E3]
- The error rate spike is due to a sudden increase in p95 latency.: The p95 latency for the service catalog in region us-east did not change significantly. [E4]
- The error rate spike is due to a configuration change.: No configuration change was observed in the evidence. [E7]
- The error rate spike is due to a dependency issue with an upstream service.: No dependency issues were observed in the evidence. [E5, E6, E8, E9]
- The error rate spike is due to a data issue.: No data issues were observed in the evidence. [E5, E6, E8, E9]
- The error rate spike is due to an infrastructure issue.: No infrastructure issues were observed in the evidence. [E5, E6, E8, E9]
- The error rate spike is due to an unknown issue.: No unknown issues were observed in the evidence. [E5, E6, E8, E9]
- The error rate spike is not due to a sudden increase in request volume.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E1]
- The error rate spike is not due to a sudden increase in p95 latency.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E4, E1]

## Actions
- (corrective, high) Roll back the deployment of catalog v2.23 to us-east.
- (preventive, high) Implement a robust error handling mechanism in the RequestHandler to prevent NullPointerExceptions.

## Fact-check
- Evidence IDs cited by the model: 26, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.41% to 3.96% (+857%), with a change point at 2026-03-07T08:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.09).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (726 per 5 min before, 891 per 5 min after, +23%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (122 ms before, 121 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v2.23 to us-east (catalog, us-east; 2 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E7** (record, deploys) Deployed catalog v1.24 to us-east (routine release) (catalog, us-east; 198 min before the change; record R010; fit: hours before the change, too early to explain a sudden jump)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v2.23) (catalog, us-east; 14 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v2.23) (catalog, us-east; 30 min after the change; record R014; fit: after the change, so a symptom, not a cause)
