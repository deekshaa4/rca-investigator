# INC-007: Why did the p95 latency go up on 04 March 2026?

## What changed
latency_p95_ms for service auth went from 90.55 to 252.6 (+179%) starting 2026-03-04T12:00:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (3 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The connection pool size change likely caused the increase in p95 latency.** (config_change, confidence 90%) [E5, E7, E8, E9]
   - Why: The auth db.pool_size was changed from 50 to 5.
   - Why: This reduction in pool size means fewer connections are available to service requests.
   - Why: With more requests than connections, the connection pool becomes exhausted, leading to increased latency.
2. **The increase in request volume could have contributed to the latency increase.** (traffic, confidence 70%) [E3]
   - Why: The request volume for service auth increased by 23%.
   - Why: With more requests, the connection pool becomes more strained.
   - Why: Exhausted connections lead to increased latency.

## Ruled out
- The increase in latency was due to a sudden spike in user traffic.: The request volume did not increase significantly, and the error rate increased instead. [E3]
- The increase in latency was caused by a new deployment.: There is no evidence of a new deployment or version change. [E1, E2, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Increase the auth db.pool_size back to 50 to improve connection handling.
- (preventive, medium) Monitor request volume and adjust the connection pool size as needed.
- (preventive, medium) Review and optimize the connection pool size for future changes.

## Fact-check
- Evidence IDs cited by the model: 14, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 91 ms to 253 ms (+179%), with a change point at 2026-03-04T12:00:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1097 per 5 min before, 1344 per 5 min after, +23%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.35% before, 0.54% after, +55%).
- **E5** (record, config_changes) Changed auth db.pool_size from 50 to 5 (all regions) (auth; 3 min before the change; record R019)
- **E6** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R021)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 13 min after the change; record R020)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 19 min after the change; record R022)
- **E9** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 24 min after the change; record R023)
