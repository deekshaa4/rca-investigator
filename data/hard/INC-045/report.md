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
1. **New deployment of search v5.23 to eu-west caused the error rate to rise.** (deployment, confidence 30%) [E1, E2, E5]
   - Why: The deployment of search v5.23 to eu-west resulted in a change in error rate.
   - Why: The error rate increased from 0.48% to 0.92%.
   - Why: The deployment happened 226 minutes before the change in error rate.
2. **No clear evidence of a configuration change that caused the error rate increase.** (unknown, confidence 30%) [E1, E2, E5]
   - Why: The deployment of search v5.23 to eu-west is the only known change.
   - Why: No other configuration changes are evident.
   - Why: The error rate increased after the deployment.

## Ruled out
- The error rate increase was due to a configuration change.: No evidence supports a configuration change. [E1, E2, E5]
- The error rate increase was due to a traffic spike.: Request volume and latency did not change significantly. [E3, E4]
- The error rate increase was due to a dependency issue with an external service.: No evidence supports a dependency issue. [E1, E2, E5]

## Actions
- (corrective, high) Roll back the deployment of search v5.23 to eu-west.
- (preventive, high) Monitor the error rate and request volume for service search in region eu-west closely.
- (preventive, medium) Review and test the new version of search v5.23 in a staging environment before full deployment.

## Fact-check
- Evidence IDs cited by the model: 14, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region eu-west rose from 0.48% to 0.92% (+91%), with a change point at 2026-03-13T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.23).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region eu-west stayed about the same (880 per 5 min before, 989 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region eu-west stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed search v5.23 to eu-west (search, eu-west; 226 min before the change; record R009)
- **E6** (record, deploys) Deployed search v2.15 to us-east (routine release) (search, us-east; 94 min before the change; record R010)
- **E7** (record, logs) catalog: INFO nightly backup completed (catalog, us-east; 336 min before the change; record R008)
