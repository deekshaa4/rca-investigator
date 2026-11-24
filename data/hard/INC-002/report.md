# INC-002: Why did the p95 latency go up on 02 March 2026?

## What changed
latency_p95_ms for service checkout went from 221.6 to 579.4 (+161%) starting 2026-03-02T10:50:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (1 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The change in db.pool_size caused the connection pool to be exhausted, leading to increased latency.** (config_change, confidence 90%) [E5, E6, E7]
   - Why: The db.pool_size was reduced from 50 to 5, causing the connection pool to be exhausted.
   - Why: With fewer connections available, the checkout service experienced longer waits for connections.
   - Why: This resulted in increased latency, as the service had to wait for connections to become available.
2. **The increase in request volume did not explain the increase in latency.** (unknown, confidence 80%) [E3, E4]
   - Why: The request volume for service checkout did not change significantly.
   - Why: The error rate increased, indicating issues within the service itself, not just increased load.

## Ruled out
- The increase in latency was due to a sudden spike in traffic.: The request volume did not change significantly, and the error rate increased, not decreased. [E3]
- The increase in latency was due to a dependency issue with an external service.: No evidence suggests the service was affected by an external service failure or slowdown. []

## Actions
- (corrective, high) Increase the db.pool_size back to 50 to ensure the connection pool is not exhausted.
- (preventive, medium) Implement a mechanism to monitor and alert on connection pool exhaustion.
- (preventive, medium) Review and optimize the checkout service's connection management to reduce the likelihood of connection pool exhaustion.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 222 ms to 579 ms (+161%), with a change point at 2026-03-02T10:50:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (817 per 5 min before, 1013 per 5 min after, +24%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.36% before, 0.53% after, +49%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R014)
- **E6** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 2 min after the change; record R015)
- **E7** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R018)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 8 min after the change; record R016)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 14 min after the change; record R017)
