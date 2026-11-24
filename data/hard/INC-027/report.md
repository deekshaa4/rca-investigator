# INC-027: Why did the p95 latency go up on 20 March 2026?

## What changed
latency_p95_ms for service auth went from 90.69 to 293 (+223%) starting 2026-03-20T04:05:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The connection pool size change likely caused the connection exhaustion warnings.** (config_change, confidence 90%) [E5, E7, E8, E9]
   - Why: The auth db.pool_size was changed from 50 to 5.
   - Why: This reduction in pool size likely caused the connection pool to exhaust more quickly.
   - Why: The connection pool exhaustion led to the WARN messages in the logs.
2. **The increase in request volume did not cause the latency spike.** (traffic, confidence 80%) [E3, E4]
   - Why: The request volume for service auth stayed about the same.
   - Why: The error rate increased, not the request volume.
   - Why: The latency spike was more pronounced than the increase in requests.

## Ruled out
- The increase in latency was due to a sudden surge in traffic.: The request volume did not change significantly. [E3]
- The latency increase was caused by a new deployment.: No alerts or error logs were present before the change. [E1, E2, E4]
- The latency increase was due to a dependency issue with an external service.: No external service failures or slowdowns were reported. [E1, E2, E4]

## Actions
- (corrective, high) Roll back the config change to restore the db.pool_size to 50.
- (preventive, medium) Monitor the connection pool size and request volume closely in the future.
- (preventive, medium) Review and optimize the connection pool configuration for the auth service.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 91 ms to 293 ms (+223%), with a change point at 2026-03-20T04:05:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1105 per 5 min before, 1235 per 5 min after, +12%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.41% before, 0.56% after, +39%).
- **E5** (record, config_changes) Changed auth db.pool_size from 50 to 5 (all regions) (auth; 2 min before the change; record R008)
- **E6** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R010)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 21 min after the change; record R011)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 24 min after the change; record R012)
- **E9** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 24 min after the change; record R013)
