# INC-025: Why did the error rate go up on 09 March 2026?

## What changed
error_rate for service auth, region eu-west went from 0.002781 to 0.006804 (+145%) starting 2026-03-09T15:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.35)
- ✗ The closest change event is 287 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New feature request may have introduced a regression.** (unknown, confidence 30%) [E5]
   - Why: Feature request R013 was submitted 287 minutes before the error rate spike.
   - Why: The feature request may have introduced a regression or unintended side effect.
   - Why: The error rate spike in service auth in region eu-west coincides with the feature request submission.
2. **Deployment of a new release may have caused the error rate spike.** (deployment, confidence 30%) [E1, E2]
   - Why: A new release was deployed at the same time as the error rate spike.
   - Why: The error rate spike in service auth in region eu-west coincides with the deployment.
   - Why: The error rate spike is concentrated in service auth in region eu-west.
3. **Configuration change may have affected the service.** (config_change, confidence 30%) [E1, E2, E3, E4]
   - Why: The error rate spike in service auth in region eu-west coincides with the deployment.
   - Why: The error rate spike is concentrated in service auth in region eu-west.
   - Why: The request volume and latency did not change significantly.

## Ruled out
- The increase in error rate was due to a sudden increase in traffic.: The request volume did not change significantly. [E3]
- The increase in error rate was due to a configuration change elsewhere in the system.: The error rate spike is concentrated in service auth in region eu-west. [E1, E2]
- The increase in error rate was due to a dependency issue with an external service.: There is no evidence of a dependency issue. [E1, E2, E3, E4]

## Actions
- (corrective, high) Review and test the new release for the service auth in region eu-west.
- (preventive, high) Monitor the system for any further errors and investigate if the error rate continues to increase.
- (preventive, medium) Review the feature request R013 and its implementation for any unintended side effects.

## Fact-check
- Evidence IDs cited by the model: 14, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region eu-west rose from 0.28% to 0.68% (+145%), with a change point at 2026-03-09T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.26).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region eu-west stayed about the same (391 per 5 min before, 439 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region eu-west stayed about the same (90 ms before, 91 ms after, +0%).
- **E5** (record, tickets) Feature request: dark mode for the account page. (catalog, eu-west; 287 min before the change; record R013)
