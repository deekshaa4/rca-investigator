# INC-034: Why did the error rate go up on 16 March 2026?

## What changed
error_rate for service search went from 0.00415 to 0.04349 (+948%) starting 2026-03-16T11:05:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (3 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Upstream search-cluster is the root cause of the error rate increase.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The error rate in service search increased after the upstream search-cluster started returning HTTP 503.
   - Why: The upstream search-cluster timeout errors were observed after the change point, indicating a problem with the upstream service.
   - Why: The error rate in service search did not change in other regions, suggesting the issue is specific to the upstream search-cluster.
2. **The increase in request volume is not the cause of the error rate increase.** (unknown, confidence 80%) [E3]
   - Why: The request volume for service search did not change significantly, with a 24% increase in requests.
   - Why: The error rate increase occurred after the change point, which is when the upstream search-cluster started returning HTTP 503.
   - Why: If the increase in request volume was the cause, we would expect to see a similar increase in error rate, but it did not happen.
3. **The increase in p95 latency is not the cause of the error rate increase.** (unknown, confidence 80%) [E4]
   - Why: The p95 latency increased by 82%, but the error rate increased by 948%. The latency increase is a symptom, not a cause.
   - Why: The error rate increase occurred after the change point, which is when the upstream search-cluster started returning HTTP 503.
   - Why: If the increase in p95 latency was the cause, we would expect to see a similar increase in error rate, but it did not happen.

## Ruled out
- The increase in error rate is due to a configuration change.: There is no evidence of a configuration change that would cause the error rate to increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in error rate is due to a deployment of a new release or version.: There is no evidence of a deployment that would cause the error rate to increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in error rate is due to a change in the data.: There is no evidence of any change in the data that would cause the error rate to increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in error rate is due to a change in the infrastructure.: There is no evidence of any change in the infrastructure that would cause the error rate to increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Investigate and fix the upstream search-cluster issue.
- (preventive, high) Monitor the upstream search-cluster status and performance closely.
- (preventive, medium) Review and optimize the request handling in service search.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.41% to 4.35% (+948%), with a change point at 2026-03-16T11:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2454 per 5 min before, 3034 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (140 ms before, 255 ms after, +82%).
- **E5** (record, alerts) Upstream search-cluster returning HTTP 503 for search (search; 3 min after the change; record R013)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 5 min after the change; record R014)
- **E7** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 14 min after the change; record R015)
- **E8** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R017)
- **E9** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 23 min after the change; record R016)
