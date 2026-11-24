# INC-022: Why did the p95 latency go up on 04 March 2026?

## What changed
latency_p95_ms for service checkout went from 220.5 to 638.3 (+190%) starting 2026-03-04T04:55:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (1 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The increase in p95 latency is due to a sudden reduction in the database pool size, leading to connection exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The database pool size was reduced from 50 to 5, causing the connection pool to be exhausted.
   - Why: This reduction in pool size led to a higher number of connection pool exhaustion warnings in the logs.
   - Why: The connection pool exhaustion caused a significant increase in p95 latency for service checkout.

## Ruled out
- The increase in p95 latency is due to a sudden increase in request volume.: The request volume for service checkout remained about the same before and after the change. [E3]
- The increase in p95 latency is due to a sudden increase in error rate.: The error rate for service checkout did not increase significantly, only by 51%. [E4]
- The increase in p95 latency is due to a sudden increase in traffic.: The request volume for service checkout did not increase significantly. [E3]

## Actions
- (corrective, high) Increase the database pool size to a more appropriate value, such as 20 or 30.
- (preventive, medium) Implement a connection pool monitoring system to detect and alert on exhaustion before it causes latency issues.
- (preventive, medium) Review and optimize the database queries to reduce the number of connections needed.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 220 ms to 638 ms (+190%), with a change point at 2026-03-04T04:55:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (819 per 5 min before, 940 per 5 min after, +15%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.46% before, 0.70% after, +51%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R009)
- **E6** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 2 min after the change; record R010)
- **E7** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 3 min after the change; record R011)
- **E8** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R013)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 7 min after the change; record R012)
