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
1. **The increase in p95 latency is due to a reduction in the database pool size, which led to connection exhaustion.** (config_change, confidence 90%) [E5, E1]
   - Why: The config_change (E5) reduced the auth db.pool_size from 50 to 5.
   - Why: This reduction in pool size caused more connections to be exhausted, leading to longer wait times.
   - Why: The longer wait times resulted in increased p95 latency (E1).
2. **The increase in p95 latency is due to the connection pool exhaustion, which is a symptom of the config_change.** (unknown, confidence 70%) [E5, E7, E8, E9, E1]
   - Why: The connection pool exhaustion (E7, E8, E9) is a symptom of the config_change (E5).
   - Why: The config_change reduced the db.pool_size, leading to connection exhaustion.
   - Why: The connection exhaustion resulted in increased p95 latency (E1).

## Ruled out
- The increase in p95 latency is due to a sudden increase in error rate.: The error rate increased by 39% (E4), but the p95 latency increased by 223% (E1). The error rate is a symptom, not a cause. [E4]
- The increase in p95 latency is due to a sudden increase in the number of users.: The request volume increased by 12% (E3), but the p95 latency increased by 223% (E1). The request volume is a symptom, not a cause. [E3]
- The increase in p95 latency is due to a sudden increase in the number of requests.: The request volume increased by 12% (E3), but the p95 latency increased by 223% (E1). The request volume is a symptom, not a cause. [E3]
- The increase in p95 latency is due to a sudden increase in request volume, which overwhelmed the system.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E1]

## Actions
- (corrective, high) Increase the db.pool_size back to 50 to prevent connection exhaustion.
- (preventive, medium) Review and optimize the database queries to reduce the number of concurrent connections.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 91 ms to 293 ms (+223%), with a change point at 2026-03-20T04:05:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1105 per 5 min before, 1235 per 5 min after, +12%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.41% before, 0.56% after, +39%).
- **E5** (record, config_changes) Changed auth db.pool_size from 50 to 5 (all regions) (auth; 2 min before the change; record R008; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R010; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 21 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 24 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 24 min after the change; record R013; fit: after the change, so a symptom, not a cause)
