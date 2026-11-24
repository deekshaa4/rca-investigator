# INC-012: Why did the p95 latency go up on 16 March 2026?

## What changed
latency_p95_ms for service auth went from 90.47 to 268.5 (+197%) starting 2026-03-16T14:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **The increase in p95 latency is due to a connection pool exhaustion issue in the auth service.** (infrastructure, confidence 30%) [E1, E4, E6, E7, E8]
   - Why: The p95 latency increased significantly (from 90 ms to 268 ms) after the change point.
   - Why: The error rate for service auth also increased (from 0.38% to 0.60%).
   - Why: Logs show warnings about connection pool exhaustion, indicating a problem with the database connections.
   - Why: evidence_ids
2. **The increase in p95 latency is due to a sudden increase in request volume for the auth service.** (traffic, confidence 30%) [E2, E3, E4]
   - Why: The p95 latency increased significantly (from 90 ms to 268 ms) after the change point.
   - Why: The request volume for service auth increased by 15% (from 1125 to 1299 per 5 min).
   - Why: The error rate for service auth also increased (from 0.38% to 0.60%).
   - Why: evidence_ids

## Ruled out
- The increase in p95 latency is due to a configuration change in the auth service.: The change in p95 latency is concentrated in service auth, and the other service/region segments stayed flat. [E2]
- The increase in p95 latency is due to a dependency issue with an external service.: There is no evidence of a failure or slowdown in any external service. []

## Actions
- (corrective, high) Implement a connection pool optimization in the auth service to handle the increased request volume.
- (preventive, medium) Monitor request volume and latency closely and take corrective action if the increase in request volume is detected.
- (preventive, medium) Review and optimize the database connection pool settings to prevent future exhaustion.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 90 ms to 268 ms (+197%), with a change point at 2026-03-16T14:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1125 per 5 min before, 1299 per 5 min after, +15%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.38% before, 0.60% after, +61%).
- **E5** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R014)
- **E6** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 5 min after the change; record R013)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 19 min after the change; record R015)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 27 min after the change; record R016)
