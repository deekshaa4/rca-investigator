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
1. **The increase in p95 latency is due to a reduction in the database pool size, leading to connection exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The database pool size was reduced from 50 to 5, causing the connection pool to be exhausted more frequently.
   - Why: This reduction in pool size means fewer connections are available to service checkout requests.
   - Why: As a result, more checkout requests are waiting for a free connection, leading to increased latency.
2. **The increase in p95 latency is also due to the increase in error rate, indicating more checkout requests are failing.** (data, confidence 80%) [E2, E3, E4]
   - Why: The error rate for checkout requests increased from 0.46% to 0.70% after the change.
   - Why: More checkout requests are failing, which contributes to the overall p95 latency increase.
   - Why: Failed requests add to the overall latency, as they require retries and additional processing time.

## Ruled out
- The increase in p95 latency is due to a sudden increase in request volume.: The request volume for checkout did not change significantly (15% increase). [E3]
- The increase in p95 latency is due to a change in traffic patterns.: There is no evidence of a sudden increase in traffic or a campaign that could explain the change. []
- The increase in p95 latency is due to a dependency issue with an external service.: There is no evidence of a failure or slowdown in any external service. []
- The increase in p95 latency is due to an infrastructure issue.: There is no evidence of any network or server capacity issues. []
- The increase in p95 latency is due to a configuration change unrelated to the database pool size.: The database pool size change is the only configuration change that occurred around the time of the change point. [E5]
- The increase in p95 latency is due to a logging issue.: There is no evidence of any logging issues or changes in logging configuration. []

## Actions
- (corrective, high) Increase the database pool size to a higher value to prevent connection exhaustion.
- (preventive, medium) Monitor the error rate for checkout requests and take corrective action if it continues to rise.
- (preventive, medium) Review and optimize the checkout process to reduce the number of failed requests.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

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
