# INC-037: Why did the p95 latency go up on 06 March 2026?

## What changed
latency_p95_ms for service search went from 140.7 to 361.7 (+157%) starting 2026-03-06T07:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.15)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✗ A traffic cause is claimed, but request volume did not rise.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **Request volume increase due to a campaign.** (traffic, confidence 30%) [E2, E3, E4]
   - Why: The request volume increased, which could have led to the connection pool exhaustion.
   - Why: The request volume increase is supported by the rise in error rate, which is often a symptom of increased load.
   - Why: The error rate increased by 56%, which is a significant jump and could be attributed to the increased load.

## Ruled out
- The increase in latency was due to a configuration change.: The latency increase is after the change point, and the configuration change evidence is not provided. [E1, E2]
- The increase in latency was due to a dependency issue with an external service.: There is no evidence of an external service failure or slowdown. [E5]
- The increase in latency was due to a configuration change.: The configuration change evidence is not provided. [E1, E2]

## Actions
- (corrective, high) Implement a connection pool monitoring and alerting system to detect and respond to exhaustion issues.
- (preventive, high) Monitor and adjust the connection pool size based on historical data and current load.
- (preventive, medium) Review and optimize the cache warming process to reduce the time it takes for the cache to warm.

## Fact-check
- Evidence IDs cited by the model: 15, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 2

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service search rose from 141 ms to 362 ms (+157%), with a change point at 2026-03-06T07:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2428 per 5 min before, 2952 per 5 min after, +22%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service search rose (0.41% before, 0.63% after, +56%).
- **E5** (record, alerts) p95 latency above SLO on search (search; 15 min after the change; record R015)
- **E6** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, eu-west; 9 min after the change; record R014)
- **E7** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, ap-south; 16 min after the change; record R016)
- **E8** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, us-east; 20 min after the change; record R017)
- **E9** (record, logs) search: INFO cache warmed in 1.8s (search, us-east; 292 min before the change; record R012)
