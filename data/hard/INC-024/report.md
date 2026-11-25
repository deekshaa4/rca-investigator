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
1. **Upstream identity-db service is experiencing degraded performance, causing auth service errors.** (dependency, confidence 90%) [E5, E9]
   - Why: The error rate in auth service increased due to upstream identity-db service returning HTTP 503 errors.
   - Why: The identity-db service is the upstream dependency of the auth service, and its degraded performance is causing the auth service to fail.
   - Why: The identity-db service is experiencing degraded performance, as evidenced by the status page stating it is investigating degraded performance.
2. **The auth service is experiencing increased latency due to upstream identity-db service.** (dependency, confidence 80%) [E4, E5]
   - Why: The p95 latency for auth service increased due to upstream identity-db service returning HTTP 503 errors.
   - Why: The increased latency is a result of the upstream identity-db service failing to respond within the expected time frame.
   - Why: The identity-db service is the upstream dependency of the auth service, and its failure is causing the auth service to experience increased latency.

## Ruled out
- The increase in error rate is due to a configuration change in the auth service.: The error rate increase is concentrated in the auth service, and the change point is at the same time as the error rate increase. [E2]
- The increase in error rate is due to a change in the traffic to the auth service.: The request volume for the auth service did not change significantly, and the error rate increase is not explained by a change in traffic. [E3]
- The increase in error rate is due to a change in the infrastructure of the auth service.: The infrastructure of the auth service did not change, and the error rate increase is not explained by a change in infrastructure. [E3]
- The increase in error rate is due to a change in the data input to the auth service.: The data input to the auth service did not change, and the error rate increase is not explained by a change in data. [E3]

## Actions
- (corrective, high) Contact the identity-db service team to investigate the degraded performance and provide a fix.
- (preventive, high) Monitor the identity-db service closely and take immediate action if it degrades again.
- (preventive, medium) Review and optimize the retry logic in the auth service to reduce the impact of upstream failures.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

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
