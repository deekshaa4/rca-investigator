# INC-037: Why did the p95 latency go up on 06 March 2026?

## What changed
latency_p95_ms for service search went from 140.7 to 361.7 (+157%) starting 2026-03-06T07:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.15)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✗ A traffic cause is claimed, but request volume did not rise.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **Request volume increase due to a campaign** (traffic, confidence 30%) [E3]
   - Why: The request volume for service search increased by 22%.
   - Why: This increase in requests put additional strain on the connection pool.
   - Why: The strain on the connection pool led to connection pool exhaustion and increased latency.

## Ruled out
- Deployment of a new release: No new release or version change is indicated by the evidence. [E1]
- Configuration change: No specific configuration change is indicated by the evidence. [E1]
- Infrastructure issue: No evidence points to an infrastructure issue, such as network or server capacity problems. [E1]
- Data quality issue: No evidence points to bad or unusual input data. [E1]
- Unknown issue: The evidence does not clearly point to a specific unknown issue. [E1]

## Actions
- (corrective, high) Implement a connection pool optimization to handle increased request volume.
- (preventive, medium) Monitor request volume and adjust the connection pool size accordingly.
- (preventive, medium) Run a campaign analysis to identify and mitigate any external factors affecting request volume.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service search rose from 141 ms to 362 ms (+157%), with a change point at 2026-03-06T07:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2428 per 5 min before, 2952 per 5 min after, +22%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service search rose (0.41% before, 0.63% after, +56%).
- **E5** (record, alerts) p95 latency above SLO on search (search; 15 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E6** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, eu-west; 9 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, ap-south; 16 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, us-east; 20 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) search: INFO cache warmed in 1.8s (search, us-east; 292 min before the change; record R012; fit: describes a symptom, not a change)
