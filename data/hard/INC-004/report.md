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
1. **Upstream search-cluster is experiencing degraded performance, causing service search to fail with HTTP 503 and timeouts.** (dependency, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The upstream search-cluster is returning HTTP 503, indicating it is down or overloaded.
   - Why: The search-cluster is failing to respond within the retries, causing service search to time out.
   - Why: The search-cluster is experiencing degraded performance, leading to the error rate increase in service search.
2. **The error rate increase is concentrated in service search, suggesting a specific issue with this service.** (unknown, confidence 80%) [E2]
   - Why: The error rate increase is not uniform across all service/region segments.
   - Why: The error rate increase is specifically in service search, indicating a localized issue.
   - Why: The localized issue in service search is likely related to the upstream search-cluster.

## Ruled out
- The increase in error rate is due to a sudden surge in user traffic.: The request volume for service search did not change significantly, and the error rate increase is concentrated in service search. [E3]
- The increase in error rate is due to a configuration change in service search.: There is no evidence of a configuration change that would cause the error rate to increase. [E1]
- The increase in error rate is due to a change in infrastructure, such as network or server capacity.: There is no evidence of a change in infrastructure that would cause the error rate to increase. [E1]
- The increase in error rate is due to bad or unusual input data.: There is no evidence of bad or unusual input data that would cause the error rate to increase. [E1]

## Actions
- (corrective, high) Investigate and fix the upstream search-cluster issue.
- (preventive, medium) Monitor the upstream search-cluster and take preemptive actions if it shows signs of degradation.
- (preventive, medium) Review and optimize the retry logic for service search.

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
