# INC-031: Why did the error rate go up on 03 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.004509 to 0.02494 (+453%) starting 2026-03-03T09:50:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of catalog v4.7 introduced a NullPointerException.** (deployment, confidence 90%) [E5, E8, E9]
   - Why: v4.7 deployment caused the error rate to rise.
   - Why: NullPointerException in RequestHandler.serialize (v4.7) triggered the error.
   - Why: The error rate spike is directly linked to the deployment of v4.7.
2. **The deployment of v4.7 was followed by a deployment of v5.11, which may have introduced the issue.** (unknown, confidence 80%) [E5, E7]
   - Why: v4.7 deployment followed by v5.11 deployment.
   - Why: v5.11 deployment may have introduced the issue.
   - Why: The error rate spike is not explained by v5.11 alone.

## Ruled out
- The increase in error rate was due to a sudden increase in request volume.: Request volume stayed about the same before and after the change. [E3]
- The increase in error rate was due to a change in latency.: p95 latency stayed about the same before and after the change. [E4]
- The increase in error rate was due to a configuration change.: No configuration change was mentioned in the evidence. []

## Actions
- (corrective, high) Roll back the deployment of catalog v4.7 to address the NullPointerException.
- (preventive, high) Monitor the system closely for any new deployments and ensure proper testing before deployment.
- (preventive, medium) Investigate the root cause of the NullPointerException in RequestHandler.serialize (v4.7).

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.45% to 2.49% (+453%), with a change point at 2026-03-03T09:50:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.13).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (727 per 5 min before, 904 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (121 ms before, 120 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v4.7 to us-east (catalog, us-east; 2 min before the change; record R013)
- **E6** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R014)
- **E7** (record, deploys) Deployed catalog v5.11 to us-east (catalog, us-east; 212 min before the change; record R012)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.7) (catalog, us-east; 21 min after the change; record R015)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.7) (catalog, us-east; 26 min after the change; record R016)
