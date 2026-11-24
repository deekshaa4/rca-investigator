# INC-029: Why did the error rate go up on 10 March 2026?

## What changed
error_rate for service auth went from 0.003924 to 0.05845 (+1390%) starting 2026-03-10T13:15:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (1 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Upstream identity-db service is experiencing degraded performance, causing auth service errors.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The error rate in auth service increased due to upstream identity-db service returning HTTP 503 errors.
   - Why: The identity-db service is the upstream dependency of the auth service, and its degraded performance is causing the auth service to fail.
   - Why: The identity-db service is experiencing timeout issues, leading to retries and eventually failing to respond within the auth service's timeout.
   - Why: evidence_ids
2. **The auth service is under higher load due to increased request volume.** (traffic, confidence 70%) [E3]
   - Why: The error rate in auth service increased despite the request volume staying about the same.
   - Why: The auth service is experiencing higher error rates despite the same request volume, indicating increased load.
   - Why: The increased load on the auth service is causing it to fail more often, leading to higher error rates.
   - Why: evidence_ids

## Ruled out
- The increase in error rate is due to a configuration change in the auth service.: The error rate increase is concentrated in the auth service, and the change point is specific to the auth service. [E1, E2]
- The increase in error rate is due to a data quality issue in the auth service.: There is no evidence of unusual input data causing the error rate increase. [E1, E2]

## Actions
- (corrective, high) Investigate and address the degraded performance of the identity-db service.
- (preventive, high) Monitor the identity-db service and implement retries or fallback mechanisms to handle transient failures.
- (preventive, medium) Optimize the auth service to handle higher request volumes.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth rose from 0.39% to 5.84% (+1390%), with a change point at 2026-03-10T13:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.33).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1114 per 5 min before, 1326 per 5 min after, +19%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth rose (90 ms before, 163 ms after, +81%).
- **E5** (record, alerts) Upstream identity-db returning HTTP 503 for auth (auth; 1 min after the change; record R016)
- **E6** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, us-east; 12 min after the change; record R017)
- **E7** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, ap-south; 18 min after the change; record R018)
- **E8** (record, tickets) identity-db status page: investigating degraded performance (auth; 30 min after the change; record R020)
- **E9** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, eu-west; 22 min after the change; record R019)
