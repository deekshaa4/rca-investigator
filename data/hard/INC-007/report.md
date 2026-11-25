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
1. **The increase in p95 latency is due to a reduction in the database pool size, leading to connection exhaustion.** (config_change, confidence 90%) [E5, E7, E8, E9]
   - Why: The config_change (E5) reduced the auth db.pool_size from 50 to 5.
   - Why: This reduction in pool size caused more connections to be exhausted, leading to the warning logs (E7, E8, E9).
   - Why: The exhausted connections resulted in longer latency, as the system had to wait for a free connection.
   - Why: evidence_ids

## Ruled out
- The increase in p95 latency is due to a configuration change in another service.: The config_change (E5) is the only change in configuration that is relevant to the auth service. [E5]
- The increase in p95 latency is due to a network issue.: There is no evidence of network issues (e.g., network latency, packet loss, etc.). []
- The increase in p95 latency is due to a dependency issue with an external service.: There is no evidence of any external service issues or changes. []
- The increase in p95 latency is due to a sudden increase in request volume, which overwhelmed the system.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E4]

## Actions
- (corrective, high) Increase the db.pool_size back to 50 to resolve the connection exhaustion issue.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 91 ms to 253 ms (+179%), with a change point at 2026-03-04T12:00:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1097 per 5 min before, 1344 per 5 min after, +23%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.35% before, 0.54% after, +55%).
- **E5** (record, config_changes) Changed auth db.pool_size from 50 to 5 (all regions) (auth; 3 min before the change; record R019; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R021; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 13 min after the change; record R020; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 19 min after the change; record R022; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 24 min after the change; record R023; fit: after the change, so a symptom, not a cause)
