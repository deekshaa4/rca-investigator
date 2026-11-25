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
1. **Upstream search-cluster is the root cause of the error rate increase.** (dependency, confidence 100%) [E5, E6, E7, E8, E9]
   - Why: The error rate in service search increased due to the upstream search-cluster returning HTTP 503.
   - Why: The upstream search-cluster is the service that the search service calls, and it is experiencing issues.
   - Why: The upstream search-cluster is the root cause of the error rate increase in service search.

## Ruled out
- The error rate increase is due to a configuration change.: There is no evidence of a configuration change that would cause the error rate to increase. [E1]
- The error rate increase is due to a sudden increase in user traffic.: The request volume for service search did not change significantly, and the error rate increase is not correlated with a spike in user traffic. [E3]
- The error rate increase is due to a data quality issue.: There is no evidence of bad or unusual input data causing the error rate increase. [E1]
- The error rate increase is due to infrastructure issues.: There is no evidence of any infrastructure issues, such as network or server capacity problems. [E1]

## Actions
- (corrective, high) Investigate and fix the upstream search-cluster issue.
- (preventive, medium) Monitor the upstream search-cluster and take preemptive actions if it shows signs of degradation.
- (preventive, medium) Review and optimize the retry logic for the search service to handle upstream failures more gracefully.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.41% to 4.35% (+948%), with a change point at 2026-03-16T11:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2454 per 5 min before, 3034 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (140 ms before, 255 ms after, +82%).
- **E5** (record, alerts) Upstream search-cluster returning HTTP 503 for search (search; 3 min after the change; record R013)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 5 min after the change; record R014)
- **E7** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 14 min after the change; record R015)
- **E8** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R017)
- **E9** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 23 min after the change; record R016)
