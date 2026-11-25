# INC-004: Why did the error rate go up on 07 March 2026?

## What changed
error_rate for service search went from 0.003516 to 0.03744 (+965%) starting 2026-03-07T05:30:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (2 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **Upstream search-cluster is returning HTTP 503 errors, causing service search error rate to spike.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The upstream search-cluster is experiencing degraded performance, indicated by the HTTP 503 errors.
   - Why: These errors are causing the service search to fail, resulting in an increase in error rate.
   - Why: The error rate increase is observed in service search, with no change in request volume or latency.
   - Why: evidence_ids
2. **Service search has a high error rate increase, coinciding with upstream search-cluster issues.** (unknown, confidence 80%) [E1, E2, E5]
   - Why: The error rate for service search has increased significantly, from 0.35% to 3.74%.
   - Why: This increase is concurrent with the upstream search-cluster returning HTTP 503 errors.
   - Why: The error rate increase is not explained by changes in request volume or latency.
   - Why: evidence_ids

## Ruled out
- The increase in error rate is due to a configuration change in service search.: The error rate increase is observed in service search, not in other services. [E2]
- The increase in error rate is due to a spike in user traffic.: The request volume for service search did not change significantly. [E3]
- The increase in error rate is due to a change in the infrastructure of service search.: The error rate increase is observed in service search, not in other services. [E2]

## Actions
- (corrective, high) Contact the upstream search-cluster team to investigate and resolve the degraded performance.
- (preventive, high) Monitor the upstream search-cluster and service search for any further issues.
- (preventive, medium) Review and optimize the error handling logic in service search to reduce the impact of upstream failures.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.35% to 3.74% (+965%), with a change point at 2026-03-07T05:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2454 per 5 min before, 2862 per 5 min after, +17%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (141 ms before, 253 ms after, +80%).
- **E5** (record, alerts) Upstream search-cluster returning HTTP 503 for search (search; 2 min after the change; record R014; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 5 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 10 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 19 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E9** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R018; fit: after the change, so a symptom, not a cause)
