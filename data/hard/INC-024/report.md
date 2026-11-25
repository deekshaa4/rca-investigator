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
1. **Upstream identity-db is experiencing degraded performance, causing auth service errors.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: identity-db returned HTTP 503, causing auth service to fail.
   - Why: auth service retries identity-db, resulting in timeout errors.
   - Why: The increased latency and error rate in auth service are a direct result of identity-db's degraded performance.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume for auth service did not change significantly. [E3]
- The increase in error rate is due to a configuration change in auth service.: The change point is marked, and the error rate increase is a result of the change. [E1, E2]
- The increase in error rate is due to a deployment of a new release in auth service.: The change point is marked, and the error rate increase is a result of the change. [E1, E2]
- The increase in error rate is due to a network issue.: No evidence supports a network issue. []
- The increase in error rate is due to a data issue.: No evidence supports a data issue. []
- The increase in error rate is due to a configuration change in another service.: No evidence supports a configuration change in another service. []
- The error rate increase is due to the change in auth service.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E1, E2]

## Actions
- (corrective, high) Investigate and fix the degraded performance of the upstream identity-db service.
- (preventive, medium) Monitor the performance of the identity-db service closely to prevent future issues.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth rose from 0.40% to 5.00% (+1146%), with a change point at 2026-03-10T09:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1080 per 5 min before, 1341 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth rose (90 ms before, 164 ms after, +81%).
- **E5** (record, alerts) Upstream identity-db returning HTTP 503 for auth (auth; 2 min after the change; record R008; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, ap-south; 5 min after the change; record R009; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, eu-west; 17 min after the change; record R010; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, us-east; 17 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E9** (record, tickets) identity-db status page: investigating degraded performance (auth; 30 min after the change; record R012; fit: after the change, so a symptom, not a cause)
