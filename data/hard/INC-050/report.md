# INC-050: Why did the error rate go up on 22 March 2026?

## What changed
error_rate for service catalog, region eu-west went from 0.005311 to 0.009589 (+81%) starting 2026-03-22T04:30:00Z. [E1, E2]

## Verdict: insufficient (score 0.37)
- ✗ The closest change event is 207 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment of search v3.8 to ap-south caused increased error rate in eu-west.** (deployment, confidence 30%) [E1, E2, E3, E4, E5, E7, E8]
   - Why: Search v3.8 deployment to ap-south increased the error rate in eu-west.
   - Why: The error rate in eu-west increased from 0.53% to 0.96%.
   - Why: The deployment to ap-south is the most recent change in the eu-west service.
   - Why: evidence_ids
2. **The new feature request for dark mode in search service caused the error rate increase.** (unknown, confidence 30%) [E1, E2, E3, E4, E5, E6, E7]
   - Why: Feature request for dark mode in search service caused the error rate increase.
   - Why: The feature request was made 130 minutes before the change.
   - Why: The feature request is the most recent change in the eu-west service.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a new deployment to eu-west.: The error rate increase is concentrated in eu-west, but the deployment to eu-west is not the cause. [E1, E2, E3, E4, E5]
- The increase in error rate was due to a new deployment to ap-south.: The error rate increase is not concentrated in ap-south, and the deployment to ap-south is not the cause. [E1, E2, E3, E4, E5, E7, E8]
- The increase in error rate was due to a new feature request in search service.: The feature request is the most recent change in the eu-west service, but the error rate increase is not due to the feature request. [E1, E2, E3, E4, E5, E6, E7]

## Actions
- (corrective, high) Roll back the deployment of search v3.8 to ap-south.
- (preventive, medium) Review and test the new feature request for dark mode in search service.
- (preventive, medium) Monitor the error rate in eu-west for any further increases and investigate promptly.

## Fact-check
- Evidence IDs cited by the model: 33, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region eu-west rose from 0.53% to 0.96% (+81%), with a change point at 2026-03-22T04:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region eu-west stayed about the same (570 per 5 min before, 648 per 5 min after, +14%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region eu-west stayed about the same (121 ms before, 121 ms after, +1%).
- **E5** (record, deploys) Deployed checkout v1.12 to eu-west (routine release) (checkout, eu-west; 207 min before the change; record R006; fit: different service/region, so unlikely to be the cause)
- **E6** (record, tickets) Feature request: dark mode for the account page. (search, ap-south; 130 min before the change; record R009; fit: different service/region, so unlikely to be the cause)
- **E7** (record, deploys) Deployed search v3.6 to eu-west (routine release) (search, eu-west; 264 min before the change; record R004; fit: different service/region, so unlikely to be the cause)
- **E8** (record, deploys) Deployed search v3.8 to ap-south (routine release) (search, ap-south; 223 min before the change; record R005; fit: different service/region, so unlikely to be the cause)
- **E9** (record, tickets) Request to add a new admin user to the dashboard. (search, us-east; 192 min before the change; record R007; fit: different service/region, so unlikely to be the cause)
