# INC-024: Why did the error rate go up on 10 March 2026?

## What changed
error_rate for service auth went from 0.004017 to 0.05003 (+1146%) starting 2026-03-10T09:30:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (2 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Upstream identity-db service is experiencing degraded performance.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The error rate for service auth increased due to upstream identity-db returning HTTP 503 errors.
   - Why: The identity-db service is the upstream dependency for service auth, causing timeouts and retries.
   - Why: The identity-db service is experiencing degraded performance, leading to the observed error rate increase.
2. **The identity-db service is underperforming.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The error rate for service auth increased due to identity-db returning HTTP 503 errors.
   - Why: The identity-db service is the upstream dependency for service auth, causing timeouts and retries.
   - Why: The identity-db service is underperforming, leading to the observed error rate increase.
3. **The identity-db service is experiencing a temporary outage.** (traffic, confidence 80%) [E5, E6, E7, E8, E9]
   - Why: The error rate for service auth increased due to identity-db returning HTTP 503 errors.
   - Why: The identity-db service is the upstream dependency for service auth, causing timeouts and retries.
   - Why: The identity-db service is experiencing a temporary outage, leading to the observed error rate increase.

## Ruled out
- The increase in error rate is due to a configuration change in service auth.: The error rate for service auth increased, but the config_change category has no supporting evidence. [E1, E2, E3, E4]
- The increase in error rate is due to a spike in request volume for service auth.: The request volume for service auth did not change significantly, as evidenced by E3. [E1, E2, E3, E4]
- The increase in error rate is due to a temporary network issue.: There is no evidence pointing to a network issue, only upstream service issues. [E1, E2, E3, E4]

## Actions
- (corrective, high) Contact identity-db support to investigate the performance degradation and potential outage.
- (preventive, high) Monitor identity-db service performance and availability closely.
- (preventive, medium) Review and optimize the retry logic for service auth in case of upstream service issues.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth rose from 0.40% to 5.00% (+1146%), with a change point at 2026-03-10T09:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1080 per 5 min before, 1341 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth rose (90 ms before, 164 ms after, +81%).
- **E5** (record, alerts) Upstream identity-db returning HTTP 503 for auth (auth; 2 min after the change; record R008)
- **E6** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, ap-south; 5 min after the change; record R009)
- **E7** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, eu-west; 17 min after the change; record R010)
- **E8** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, us-east; 17 min after the change; record R011)
- **E9** (record, tickets) identity-db status page: investigating degraded performance (auth; 30 min after the change; record R012)
