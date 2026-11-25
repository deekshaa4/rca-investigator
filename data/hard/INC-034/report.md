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
1. **Upstream search-cluster is returning HTTP 503, causing service search error rate to spike.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: Upstream search-cluster is experiencing degraded performance, leading to HTTP 503 errors.
   - Why: These errors cause service search to fail, increasing error rate.
   - Why: The error rate increase is observed in service search, with no other service/region segments changing significantly.

## Ruled out
- The increase in request volume is causing the error rate to rise.: Request volume for service search stayed about the same, with a 24% increase in p95 latency. [E3]
- The error rate increase is due to a configuration change in service search.: No configuration change is noted in the evidence. []
- The error rate increase is due to a deployment of a new release or version in service search.: No deployment is noted in the evidence. []
- Service search's p95 latency is increasing, indicating degraded performance.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E2, E3, E4]

## Actions
- (corrective, high) Investigate and address the degraded performance of the upstream search-cluster.
- (preventive, medium) Monitor and optimize the performance of the upstream search-cluster.

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.41% to 4.35% (+948%), with a change point at 2026-03-16T11:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2454 per 5 min before, 3034 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (140 ms before, 255 ms after, +82%).
- **E5** (record, alerts) Upstream search-cluster returning HTTP 503 for search (search; 3 min after the change; record R013; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 5 min after the change; record R014; fit: describes a symptom, not a change)
- **E7** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 14 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E8** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 23 min after the change; record R016; fit: after the change, so a symptom, not a cause)
