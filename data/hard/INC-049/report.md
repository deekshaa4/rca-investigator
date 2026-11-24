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
   - Why: Upstream payments-api timeouts after retries, causing service checkout errors (E6, E7, E8).
   - Why: Payments-api status page reports degraded performance (E9).
   - Why: evidence_ids
2. **Service checkout request volume increased, leading to higher error rate.** (traffic, confidence 70%) [E3, E1]
   - Why: Request volume for service checkout increased by 12% (E3).
   - Why: Increased request volume puts more strain on the system, leading to higher error rate (E1).
   - Why: evidence_ids

## Ruled out
- The error rate increase is due to a configuration change.: No evidence supports a configuration change (E1, E2, E3, E4, E5, E6, E7, E8, E9). [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The error rate increase is due to a data quality issue.: No evidence supports a data quality issue (E1, E2, E3, E4, E5, E6, E7, E8, E9). [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The error rate increase is due to a deployment or version change.: No evidence supports a deployment or version change (E1, E2, E3, E4, E5, E6, E7, E8, E9). [E1, E2, E3, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Implement retries and timeouts for upstream payments-api calls to handle transient failures.
- (preventive, high) Monitor payments-api performance and alert on degraded performance.
- (preventive, medium) Optimize service checkout request handling to reduce error rate.

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
