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
1. **Config change to reduce db.pool_size from 50 to 5, leading to connection pool exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The config change reduced the connection pool size, causing more connections to be exhausted.
   - Why: With fewer connections available, the pool could not handle the increased load, leading to exhaustion.
   - Why: This exhaustion resulted in the warning messages observed in the logs.

## Ruled out
- Deployment of a new release or version caused the change.: No evidence of a new release or version deployment was found. []
- External dependency failure caused the change.: No evidence of an external service failure or slowdown was found. []
- Infrastructure issues caused the change.: No evidence of network or capacity issues was found. []
- Data issues caused the change.: No evidence of bad or unusual input data was found. []
- Increased request volume for service checkout.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E4]

## Actions
- (corrective, high) Roll back the config change to 50 pool size and monitor the system.
- (preventive, high) Implement a connection pool monitoring and alerting system to detect exhaustion early.
- (preventive, medium) Optimize the database queries to reduce the number of connections needed.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 220 ms to 638 ms (+190%), with a change point at 2026-03-04T04:55:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (819 per 5 min before, 940 per 5 min after, +15%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.46% before, 0.70% after, +51%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R009; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 2 min after the change; record R010; fit: describes a symptom, not a change)
- **E7** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 3 min after the change; record R011; fit: describes a symptom, not a change)
- **E8** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 7 min after the change; record R012; fit: after the change, so a symptom, not a cause)
