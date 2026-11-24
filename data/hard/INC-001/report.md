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
1. **New deployment of search v2.20 caused the error rate to spike.** (deployment, confidence 90%) [E5, E1]
   - Why: The deployment of search v2.20 introduced a new version of the service.
   - Why: This new version was deployed 4 minutes before the error rate spike.
   - Why: The error rate increased significantly after the deployment, indicating the deployment was the cause.
2. **NullPointerException in RequestHandler.serialize caused the error.** (unknown, confidence 80%) [E7, E8, E5]
   - Why: The deployment of search v2.20 introduced a new version of the service.
   - Why: This new version caused a NullPointerException in RequestHandler.serialize.
   - Why: This NullPointerException led to the error rate spike.

## Ruled out
- The increase in request volume caused the error rate spike.: The request volume stayed about the same before and after the change. [E3]
- The increase in p95 latency caused the error rate spike.: The p95 latency stayed about the same before and after the change. [E4]
- The deployment of catalog v6.12 caused the error rate spike.: The deployment of catalog v6.12 happened 4 minutes before the change, not 4 minutes after. [E9]

## Actions
- (corrective, high) Fix the NullPointerException in RequestHandler.serialize in the new search v2.20 version.
- (preventive, medium) Monitor the error rate and request volume closely after any deployment to ap-south.
- (preventive, medium) Review and test the new search v2.20 version in a staging environment before deploying to production.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.34% to 2.99% (+791%), with a change point at 2026-03-26T06:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.17).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south stayed about the same (506 per 5 min before, 603 per 5 min after, +19%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed search v2.20 to ap-south (search, ap-south; 4 min before the change; record R011)
- **E6** (record, alerts) High error rate on search in ap-south (search, ap-south; 10 min after the change; record R014)
- **E7** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 2 min after the change; record R013)
- **E8** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 22 min after the change; record R015)
- **E9** (record, deploys) Deployed catalog v6.12 to eu-west (catalog, eu-west; 4 min before the change; record R012)
