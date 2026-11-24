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
1. **The deployment of catalog v2.23 caused the error rate to spike.** (deployment, confidence 90%) [E5, E8, E9]
   - Why: The deployment of catalog v2.23 introduced a new version of the service.
   - Why: The new version (v2.23) had a NullPointerException in RequestHandler.serialize.
   - Why: This NullPointerException led to an increase in error rate.
2. **The deployment of catalog v1.24 did not cause the error rate to spike.** (deployment, confidence 90%) [E7, E1]
   - Why: The deployment of catalog v1.24 was a routine release.
   - Why: It did not introduce any new issues.
   - Why: The error rate did not change significantly after this deployment.

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The increase in error rate was due to a configuration change.: No configuration change was recorded around the time of the error rate increase. [E1, E2, E3, E4]

## Actions
- (corrective, high) Fix the NullPointerException in RequestHandler.serialize in the v2.23 version of the service.
- (preventive, high) Implement a monitoring system to detect and alert on NullPointerExceptions in the RequestHandler.serialize method.
- (preventive, medium) Review and stabilize the deployment process to ensure that only stable versions are released to production.

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
