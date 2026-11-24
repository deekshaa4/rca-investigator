# INC-001: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service search, region ap-south went from 0.003315 to 0.02985 (+800%) starting 2026-03-26T06:20:00Z. [E1, E2]

## Verdict: sufficient (score 0.94)
- A change event (deploys) matches the affected segment and timing (4 min before the change; matches the affected segment).

## Why it happened
1. **The deployment of search v2.20 caused an increase in error rate and request volume.** (deployment, confidence 90%) [E5, E7, E8, E9]
   - Why: Deployed search v2.20 to ap-south (R011).
   - Why: The deployment introduced a NullPointerException in RequestHandler.serialize (R012, R014, R015).
   - Why: NullPointerException led to increased error rate and request volume (E1, E2, E3).
2. **The increase in request volume may have contributed to the error rate increase.** (traffic, confidence 70%) [E2, E3, E1]
   - Why: Request volume for service search in region ap-south increased (E2, E3).
   - Why: Increased request volume could have overwhelmed the system, leading to more errors (E1).

## Ruled out
- The increase in error rate was due to a change in user behavior.: No evidence suggests a change in user behavior around the time of the error rate increase (no user behavior logs or metrics). []
- The increase in error rate was due to a change in the system configuration.: The error rate increase coincides with the deployment of a new version of the search service (E5), not with any configuration changes (no other configuration-related evidence). [E5]

## Actions
- (corrective, high) Roll back the deployment of search v2.20 to ap-south.
- (preventive, medium) Monitor request volume and error rate closely in ap-south and take preemptive measures if volume spikes again.
- (corrective, high) Investigate and fix the root cause of the NullPointerException in RequestHandler.serialize.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.33% to 2.98% (+800%), with a change point at 2026-03-26T06:20:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.20).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south rose (504 per 5 min before, 597 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (141 ms before, 139 ms after, -1%).
- **E5** (record, deploys) Deployed search v2.20 to ap-south (search, ap-south; 4 min before the change; record R011)
- **E6** (record, alerts) High error rate on search in ap-south (search, ap-south; 10 min after the change; record R013)
- **E7** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 2 min after the change; record R012)
- **E8** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 22 min after the change; record R014)
- **E9** (record, logs) search: ERROR NullPointerException in RequestHandler.serialize (v2.20) (search, ap-south; 40 min after the change; record R015)
