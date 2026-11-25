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
   - Why: payments-api returns HTTP 503, indicating degraded performance (E5).
   - Why: checkout service experiences errors due to upstream payments-api timeout (E6, E7, E8).
   - Why: payments-api status page shows degraded performance (E9).
   - Why: evidence_ids

## Ruled out
- The increase in error rate is due to a sudden increase in request volume.: Request volume for service checkout stayed about the same (E3). [E3]
- The increase in error rate is due to a sudden increase in users or requests.: The error rate increase is not due to changes in other services (E2). [E2]
- The increase in error rate is due to a sudden increase in latency.: The p95 latency for service checkout rose (E4). [E4]
- The error rate increase is due to a configuration change in the checkout service.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E1, E2]

## Actions
- (preventive, high) Monitor payments-api for any future performance issues.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout rose from 0.46% to 3.72% (+717%), with a change point at 2026-03-12T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.17).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (849 per 5 min before, 955 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout rose (220 ms before, 399 ms after, +81%).
- **E5** (record, alerts) Upstream payments-api returning HTTP 503 for checkout (checkout; 2 min after the change; record R014; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, ap-south; 3 min after the change; record R015; fit: describes a symptom, not a change)
- **E7** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, us-east; 8 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) checkout: ERROR upstream payments-api timeout after 3 retries (checkout, eu-west; 12 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E9** (record, tickets) payments-api status page: investigating degraded performance (checkout; 30 min after the change; record R018; fit: after the change, so a symptom, not a cause)
