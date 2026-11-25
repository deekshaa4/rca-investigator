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
1. **New deployment of catalog v2.23 introduced a NullPointerException.** (deployment, confidence 90%) [E5, E8, E9]
   - Why: v2.23 deployment caused the error rate to rise.
   - Why: NullPointerException in RequestHandler.serialize (v2.23) triggered the error.
   - Why: Increased error rate led to higher error rate metric.
2. **No significant change in request volume or latency, suggesting the issue is not related to traffic or infrastructure.** (unknown, confidence 80%) [E3, E4]
   - Why: Request volume and latency remained stable.
   - Why: No significant change in error rate despite increased volume.
   - Why: Error rate increase is not due to traffic or infrastructure issues.

## Ruled out
- The increase in error rate is due to a sudden spike in user traffic.: Request volume and latency remained stable. [E3, E4]
- The increase in error rate is due to a configuration change.: No configuration change was observed. [E7]
- The increase in error rate is due to a dependency issue with an external service.: No external service issues were observed. [E8, E9]

## Actions
- (corrective, high) Fix the NullPointerException in RequestHandler.serialize in v2.23
- (preventive, medium) Implement a robust error handling mechanism in RequestHandler.serialize
- (preventive, medium) Monitor the RequestHandler.serialize method for future occurrences

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.41% to 3.96% (+857%), with a change point at 2026-03-07T08:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.09).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (726 per 5 min before, 891 per 5 min after, +23%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (122 ms before, 121 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v2.23 to us-east (catalog, us-east; 2 min before the change; record R011)
- **E6** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R012)
- **E7** (record, deploys) Deployed catalog v1.24 to us-east (routine release) (catalog, us-east; 198 min before the change; record R010)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v2.23) (catalog, us-east; 14 min after the change; record R013)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v2.23) (catalog, us-east; 30 min after the change; record R014)
