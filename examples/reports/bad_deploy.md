# INC-001: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service search, region ap-south went from 0.003315 to 0.02985 (+800%) starting 2026-03-26T06:20:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (4 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment caused the error rate to spike.** (deployment, confidence 90%) [E5, E7, E8, E9]
   - Why: The deployment of search v2.20 to ap-south introduced a new version of the RequestHandler.
   - Why: The new version of RequestHandler had a NullPointerException, leading to errors.
   - Why: These errors caused the error rate to rise significantly.

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: Request volume and p95 latency remained stable, contradicting this hypothesis. [E3, E4]
- The error rate increase was caused by a configuration change.: No evidence supports a config change, only a deployment. [E1, E2, E5]
- The error rate increase was due to a dependency issue with an external service.: No evidence points to an external service failure or slowdown. [E1, E2, E5]

## Actions
- (corrective, high) Fix the NullPointerException in the RequestHandler of search v2.20
- (preventive, high) Implement a robust error handling mechanism in the RequestHandler
- (preventive, medium) Monitor the RequestHandler for similar issues in future deployments

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.33% to 2.98% (+800%), with a change point at 2026-03-26T06:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.20).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south stayed about the same (504 per 5 min before, 597 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (141 ms before, 139 ms after, -1%).
- **E5** (record, deploys) Deployed search v2.20 to ap-south (search, ap-south; 4 min before the change; record R011)
- **E6** (record, alerts) High error rate on search in ap-south (search, ap-south; 10 min after the change; record R013)
- **E7** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 2 min after the change; record R012)
- **E8** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 22 min after the change; record R014)
- **E9** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 40 min after the change; record R015)
