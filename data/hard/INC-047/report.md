# INC-047: Why did the p95 latency go up on 22 March 2026?

## What changed
latency_p95_ms for service checkout went from 220.9 to 692.8 (+214%) starting 2026-03-22T13:05:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Config change increased db.pool_size from 50 to 5, causing connection pool exhaustion.** (config_change, confidence 90%) [E5, E7, E8, E9]
   - Why: The config change reduced the pool size, leading to a larger number of concurrent connections.
   - Why: With fewer connections available, the pool exhausted more quickly, causing waiting.
   - Why: Waiting for a free connection increased p95 latency.

## Ruled out
- The increase in error rate was due to the config change.: The error rate increased after the change, but the config change happened before the error rate increase. [E4, E5]
- The increase in p95 latency was due to a spike in user activity.: The error rate increased after the change, but the error rate spike happened after the p95 latency increase. [E4, E5]
- The increase in p95 latency was due to a network issue.: There were no network-related logs or alerts, and the issue was specific to the database connection pool. [E6, E7, E8, E9]
- Request volume increase led to more connections being made, exacerbating the pool exhaustion.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E4]

## Actions
- (corrective, high) Reduce db.pool_size back to 50 to mitigate connection pool exhaustion.
- (preventive, medium) Implement connection pooling optimization or increase db.pool_size if needed.

## Fact-check
- Evidence IDs cited by the model: 14, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 221 ms to 693 ms (+214%), with a change point at 2026-03-22T13:05:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (833 per 5 min before, 997 per 5 min after, +20%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.33% before, 0.49% after, +49%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 2 min before the change; record R009; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 6 min after the change; record R010; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 20 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 21 min after the change; record R013; fit: after the change, so a symptom, not a cause)
