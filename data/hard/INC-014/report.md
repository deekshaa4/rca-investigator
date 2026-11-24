# INC-014: Why did the error rate go up on 02 March 2026?

## What changed
error_rate for service search went from 0.003606 to 0.03658 (+914%) starting 2026-03-02T14:05:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
No contributing factor is supported by the evidence.

## Ruled out
- The increase in error rate is due to a configuration change.: The error rate increase is specific to service search and not affecting other services, indicating a targeted issue rather than a broad configuration change. [E1, E2]
- The increase in error rate is due to a sudden increase in user traffic.: The request volume for service search did not change significantly, with a 17% increase in requests per 5 minutes. [E3]
- The increase in error rate is due to a sudden increase in data quality.: There is no evidence of unusual input data causing the error rate increase. [E8]

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.36% to 3.66% (+914%), with a change point at 2026-03-02T14:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.14).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2520 per 5 min before, 2942 per 5 min after, +17%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (140 ms before, 252 ms after, +79%).
- **E5** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 16 min after the change; record R013)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 18 min after the change; record R014)
- **E7** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R016)
- **E8** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 25 min after the change; record R015)
