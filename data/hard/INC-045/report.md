# INC-045: Why did the error rate go up on 13 March 2026?

## What changed
error_rate for service search, region eu-west went from 0.004807 to 0.009203 (+91%) starting 2026-03-13T15:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 226 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment of search v5.23 to eu-west caused the error rate to increase.** (deployment, confidence 30%) [E1, E2, E5]
   - Why: search v5.23 deployment introduced a new error condition.
   - Why: The error condition propagated to the error rate metric.
   - Why: The error rate metric increased from 0.48% to 0.92%.
   - Why: evidence_ids
2. **The increase in error rate is not due to a sudden increase in request volume or latency.** (unknown, confidence 30%) [E3, E4]
   - Why: Request volume and latency remained stable before and after the change.
   - Why: The error rate increase is not correlated with changes in request volume or latency.
   - Why: The error rate increase is a standalone issue.
   - Why: evidence_ids

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: Request volume and latency remained stable before and after the change. [E3, E4]
- The increase in error rate is due to a configuration change.: The deployment record R009 indicates a new deployment, not a configuration change. [E5]
- The increase in error rate is due to a dependency issue with an external service.: No evidence suggests the error rate increase is due to a failure or slowdown of an external service. [E6]

## Actions
- (corrective, high) Roll back the search v5.23 deployment to eu-west.
- (preventive, high) Monitor the error rate and request volume for any further anomalies.
- (preventive, medium) Review the new search v5.23 release notes for any known issues.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region eu-west rose from 0.48% to 0.92% (+91%), with a change point at 2026-03-13T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.23).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region eu-west stayed about the same (880 per 5 min before, 989 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region eu-west stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed search v5.23 to eu-west (search, eu-west; 226 min before the change; record R009)
- **E6** (record, deploys) Deployed search v2.15 to us-east (routine release) (search, us-east; 94 min before the change; record R010)
- **E7** (record, logs) catalog: INFO nightly backup completed (catalog, us-east; 336 min before the change; record R008)
