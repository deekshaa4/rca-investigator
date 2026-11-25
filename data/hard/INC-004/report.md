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
1. **Upstream search-cluster is returning HTTP 503 and experiencing timeouts.** (dependency, confidence 100%) [E5, E6, E7, E8, E9]
   - Why: The upstream search-cluster is the source of the error rate increase.
   - Why: The search-cluster is returning HTTP 503, indicating a service failure.
   - Why: The search-cluster is experiencing timeouts, causing retries and increased latency.
2. **Request volume for service search is increasing, but not enough to explain the error rate increase.** (traffic, confidence 80%) [E2, E3]
   - Why: The error rate increase is concentrated in service search, not all services.
   - Why: The request volume for service search is only slightly higher after the change.
   - Why: The error rate increase is more pronounced than the request volume increase.

## Ruled out
- The error rate increase is due to a configuration change.: No evidence supports a configuration change. [E1]
- The error rate increase is due to a data issue.: No evidence supports a data issue. [E1]
- The error rate increase is due to a deployment issue.: The error rate increase is after the deployment, not before. [E1]

## Actions
- (corrective, high) Contact the upstream search-cluster team to investigate the service failure and timeouts.
- (preventive, high) Monitor the upstream search-cluster and take immediate action if it shows signs of failure again.
- (preventive, medium) Review and optimize the request handling logic for service search to better handle increased load.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.35% to 3.74% (+965%), with a change point at 2026-03-07T05:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2454 per 5 min before, 2862 per 5 min after, +17%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (141 ms before, 253 ms after, +80%).
- **E5** (record, alerts) Upstream search-cluster returning HTTP 503 for search (search; 2 min after the change; record R014)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 5 min after the change; record R015)
- **E7** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 10 min after the change; record R016)
- **E8** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 19 min after the change; record R017)
- **E9** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R018)
