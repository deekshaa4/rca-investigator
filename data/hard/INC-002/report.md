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
1. **Config change to reduce db.pool_size from 50 to 5, causing connection pool exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The config change reduced the connection pool size, leading to exhaustion.
   - Why: With fewer connections available, the pool could not handle the increased request volume.
   - Why: This resulted in the connection pool exhaustion warnings and increased latency.

## Ruled out
- External service failure or slowdown caused the issue.: No evidence of external service issues or slowdowns is provided. []
- Data quality issues caused the latency increase.: No evidence of bad or unusual input data is provided. []
- Infrastructure issues caused the latency increase.: No evidence of server, network, or capacity issues is provided. []
- Increased request volume for service checkout.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E2, E3]

## Actions
- (corrective, high) Roll back the config change to db.pool_size to 50 and monitor the system.
- (preventive, high) Implement a connection pool monitoring and alerting system to detect exhaustion early.
- (preventive, medium) Optimize the connection pool size based on historical request patterns.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 222 ms to 579 ms (+161%), with a change point at 2026-03-02T10:50:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (817 per 5 min before, 1013 per 5 min after, +24%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.36% before, 0.53% after, +49%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R014; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 2 min after the change; record R015; fit: describes a symptom, not a change)
- **E7** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R018; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 8 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 14 min after the change; record R017; fit: after the change, so a symptom, not a cause)
