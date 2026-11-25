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
1. **The increase in p95 latency is due to a reduction in the database pool size, leading to connection exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The config_change (E5) reduced the db.pool_size from 50 to 5.
   - Why: This reduction in pool size caused the connection pool to become exhausted more quickly.
   - Why: The increased latency and error rate (E2, E4, E6, E7, E8, E9) are symptoms of the connection pool exhaustion.
2. **The increase in p95 latency is also due to the increase in request volume, which put more pressure on the system.** (traffic, confidence 80%) [E3, E6, E7, E8, E9]
   - Why: The request volume for service checkout increased by 24% (E3).
   - Why: The increased request volume put more pressure on the system, exacerbating the connection pool exhaustion.
   - Why: The connection pool exhaustion (E6, E7, E8, E9) caused the p95 latency to rise.

## Ruled out
- The increase in p95 latency is due to a change in the service configuration.: The config_change (E5) was the only change made to the system before the p95 latency increase, and the increase in p95 latency is not a direct result of the config_change. [E5]
- The increase in p95 latency is due to a change in the service's external dependencies.: There is no evidence that the service's external dependencies changed or failed around the time of the p95 latency increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in p95 latency is due to a change in the service's infrastructure.: There is no evidence that the service's infrastructure changed or failed around the time of the p95 latency increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Increase the db.pool_size back to 50 to prevent connection pool exhaustion.
- (preventive, medium) Monitor request volume and adjust capacity if necessary to prevent connection pool exhaustion.

## Fact-check
- Evidence IDs cited by the model: 29, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

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
