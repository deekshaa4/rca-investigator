# INC-032: Why did the p95 latency go up on 05 March 2026?

## What changed
latency_p95_ms for service search went from 140.2 to 290.1 (+107%) starting 2026-03-05T03:15:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Config change increased the pool size, leading to connection exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: Config change increased search db.pool_size from 50 to 5.
   - Why: Connection pool size reduction led to exhaustion during high request volume.
   - Why: High request volume caused the connection pool to exhaust, resulting in latency increase.

## Ruled out
- External dependency failure caused the latency increase.: No evidence of external service failure or slowdown. []
- Infrastructure issue caused the latency increase.: No evidence of network or server issues. []
- Data quality issues caused the latency increase.: No evidence of bad input data. []
- Increased request volume caused the connection pool to exhaust.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E4]

## Actions
- (corrective, high) Roll back the config change to restore the original pool size of 50.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service search rose from 140 ms to 290 ms (+107%), with a change point at 2026-03-05T03:15:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2514 per 5 min before, 2741 per 5 min after, +9%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service search rose (0.40% before, 0.62% after, +53%).
- **E5** (record, config_changes) Changed search db.pool_size from 50 to 5 (all regions) (search; 2 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, eu-west; 3 min after the change; record R012; fit: describes a symptom, not a change)
- **E7** (record, alerts) p95 latency above SLO on search (search; 15 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, ap-south; 20 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, us-east; 26 min after the change; record R015; fit: after the change, so a symptom, not a cause)
