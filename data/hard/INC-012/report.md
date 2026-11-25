# INC-012: Why did the p95 latency go up on 16 March 2026?

## What changed
latency_p95_ms for service auth went from 90.47 to 268.5 (+197%) starting 2026-03-16T14:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **The connection pool exhaustion warnings indicate a bottleneck in database connections.** (dependency, confidence 30%) [E2, E3, E4, E5, E6, E7, E8]
   - Why: The increase in p95 latency is due to the connection pool exhaustion warnings.
   - Why: The connection pool exhaustion is caused by the increase in request volume for service auth.
   - Why: The increase in request volume is likely due to the rise in p95 latency, creating a feedback loop.
2. **The service auth request volume increased, leading to connection pool exhaustion.** (traffic, confidence 30%) [E2, E3, E4, E5, E6, E7, E8]
   - Why: The rise in p95 latency is caused by the connection pool exhaustion warnings.
   - Why: The connection pool exhaustion is due to the increase in request volume for service auth.
   - Why: The increase in request volume is likely due to the rise in p95 latency, creating a feedback loop.
3. **The service auth request volume increased, leading to connection pool exhaustion.** (traffic, confidence 30%) [E2, E3, E4, E5, E6, E7, E8]
   - Why: The rise in p95 latency is caused by the connection pool exhaustion warnings.
   - Why: The connection pool exhaustion is due to the increase in request volume for service auth.
   - Why: The increase in request volume is likely due to the rise in p95 latency, creating a feedback loop.

## Ruled out
- The increase in p95 latency is due to a configuration change in service auth.: The change in p95 latency is concentrated in service auth, but the other service/region segments stayed flat. [E2]
- The increase in p95 latency is due to a deployment of a new release or version in service auth.: The change in p95 latency is concentrated in service auth, but there is no evidence of a deployment. [E1]
- The increase in p95 latency is due to a data issue, such as bad or unusual input data.: There is no evidence of unusual input data. [E1, E2, E3, E4, E5, E6, E7, E8]
- The increase in p95 latency is due to an infrastructure issue, such as a server or network problem.: There is no evidence of an infrastructure issue. [E1, E2, E3, E4, E5, E6, E7, E8]
- The increase in p95 latency is due to a configuration change in the upstream service.: There is no evidence of a configuration change in the upstream service. [E1, E2, E3, E4, E5, E6, E7, E8]

## Actions
- (corrective, high) Implement a connection pool monitoring and alerting system to detect and respond to connection pool exhaustion warnings in a timely manner.
- (preventive, high) Monitor and optimize the database connection pool size to prevent exhaustion.
- (preventive, high) Implement a traffic management system to control and distribute request volume for service auth.

## Fact-check
- Evidence IDs cited by the model: 47, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 90 ms to 268 ms (+197%), with a change point at 2026-03-16T14:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1125 per 5 min before, 1299 per 5 min after, +15%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.38% before, 0.60% after, +61%).
- **E5** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R014)
- **E6** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 5 min after the change; record R013)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 19 min after the change; record R015)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 27 min after the change; record R016)
