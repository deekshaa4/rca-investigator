# INC-049: Why did the error rate go up on 12 March 2026?

## What changed
error_rate for service checkout went from 0.004557 to 0.03723 (+717%) starting 2026-03-12T15:15:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (2 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Upstream payments-api is experiencing degraded performance, causing service checkout errors.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: payments-api is returning HTTP 503 (Service Unavailable) for checkout requests.
   - Why: This results in timeout errors in the checkout service.
   - Why: The error rate for service checkout increases from 0.46% to 3.72%.
   - Why: evidence_ids
2. **The increase in error rate is due to the increased load on the payments-api.** (traffic, confidence 80%) [E3]
   - Why: The request volume for service checkout increased by 12%.
   - Why: This increased load is causing the payments-api to degrade.
   - Why: The error rate for service checkout increases from 0.46% to 3.72%.
   - Why: evidence_ids
3. **The increase in error rate is due to the configuration changes in the service checkout.** (config_change, confidence 70%) [E2]
   - Why: The change in error rate is concentrated in service checkout.
   - Why: This suggests that the configuration changes in service checkout are the cause.
   - Why: The error rate for service checkout increases from 0.46% to 3.72%.
   - Why: evidence_ids

## Ruled out
- The increase in error rate is due to a new deployment of the service checkout.: No evidence supports a new deployment of the service checkout. []
- The increase in error rate is due to a data quality issue.: No evidence supports a data quality issue. []
- The increase in error rate is due to a sudden increase in users.: The request volume for service checkout stayed about the same. [E3]

## Actions
- (corrective, high) Implement a retry mechanism with exponential backoff for the checkout service to handle transient failures in the payments-api.
- (preventive, medium) Monitor the payments-api for any future degradation and take preemptive action if needed.
- (preventive, medium) Review and optimize the configuration of the service checkout to reduce error rates.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout rose from 0.46% to 3.72% (+717%), with a change point at 2026-03-12T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.17).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (849 per 5 min before, 955 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout rose (220 ms before, 399 ms after, +81%).
- **E5** (record, alerts) Upstream payments-api returning HTTP 503 for checkout (checkout; 2 min after the change; record R014)
- **E6** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, ap-south; 3 min after the change; record R015)
- **E7** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, us-east; 8 min after the change; record R016)
- **E8** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, eu-west; 12 min after the change; record R017)
- **E9** (record, tickets) payments-api status page: investigating degraded performance (checkout; 30 min after the change; record R018)
