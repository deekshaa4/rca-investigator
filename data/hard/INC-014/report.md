# INC-014: Why did the error rate go up on 02 March 2026?

## What changed
error_rate for service search went from 0.003606 to 0.03658 (+914%) starting 2026-03-02T14:05:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **New deployment caused the error rate to spike.** (deployment, confidence 30%) [E1, E2]
   - Why: The change point coincides with a deployment that introduced a new version of the service.
   - Why: The error rate increased sharply, indicating a new issue was introduced.
   - Why: The error rate spike is concentrated in service search, suggesting the issue is specific to this service.

## Ruled out
- Configuration change caused the error rate to spike.: No configuration change is mentioned in the evidence. [E1, E2, E3, E4, E5, E6, E7, E8]
- Increased traffic caused the error rate to spike.: Request volume stayed about the same, and the error rate increase is not explained by more users. [E1, E2, E3, E4, E5, E6, E7, E8]
- Infrastructure issue caused the error rate to spike.: No evidence points to an infrastructure issue, such as network or server capacity problems. [E1, E2, E3, E4, E5, E6, E7, E8]
- Data quality issue caused the error rate to spike.: No evidence points to bad or unusual input data. [E1, E2, E3, E4, E5, E6, E7, E8]
- Unknown issue caused the error rate to spike.: No other plausible explanations are ruled out. [E1, E2, E3, E4, E5, E6, E7, E8]

## Actions
- (corrective, high) Investigate and fix the upstream search-cluster issue.
- (preventive, medium) Monitor the upstream search-cluster for similar issues in the future.
- (preventive, medium) Review and optimize the deployment process to prevent similar issues in the future.

## Fact-check
- Evidence IDs cited by the model: 46, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search rose from 0.36% to 3.66% (+914%), with a change point at 2026-03-02T14:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.14).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2520 per 5 min before, 2942 per 5 min after, +17%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search rose (140 ms before, 252 ms after, +79%).
- **E5** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, ap-south; 16 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E6** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, eu-west; 18 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E7** (record, tickets) search-cluster status page: investigating degraded performance (search; 30 min after the change; record R016; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) search: ERROR upstream search-cluster timeout after 3 retries (search, us-east; 25 min after the change; record R015; fit: after the change, so a symptom, not a cause)
