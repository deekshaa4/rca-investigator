# INC-020: Why did the error rate go up on 21 March 2026?

## What changed
error_rate for service search, region ap-south went from 0.004825 to 0.01069 (+122%) starting 2026-03-21T11:55:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 217 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment caused the error rate to increase.** (deployment, confidence 30%) [E5, E1]
   - Why: search v7.6 deployment introduced changes to the service search in region ap-south.
   - Why: The error rate increased from 0.48% to 1.07% after the deployment.
   - Why: The error rate increase is concentrated in service search in region ap-south, where the deployment occurred.
2. **The deployment may have introduced a new issue that affected the error rate.** (unknown, confidence 30%) [E5, E1]
   - Why: The deployment of search v7.6 did not affect the request volume or latency.
   - Why: The error rate increase is not explained by changes in request volume or latency.
   - Why: The error rate increase is specific to the service search in region ap-south, which is where the deployment occurred.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume did not change significantly, and the error rate increase is specific to the service search in region ap-south. [E3]
- The increase in error rate is due to a problem with the upstream service.: The deployment of search v7.6 did not affect the latency, and the error rate increase is specific to the service search in region ap-south. [E4]

## Actions
- (corrective, high) Roll back the search v7.6 deployment to revert the changes.
- (preventive, medium) Monitor the service search in region ap-south for any further issues and take appropriate action.
- (preventive, medium) Review and test the deployment process to ensure it is robust and can handle changes without affecting other services.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.48% to 1.07% (+122%), with a change point at 2026-03-21T11:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.18).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south stayed about the same (511 per 5 min before, 627 per 5 min after, +23%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (140 ms before, 138 ms after, -2%).
- **E5** (record, deploys) Deployed search v7.6 to ap-south (search, ap-south; 217 min before the change; record R009)
- **E6** (record, logs) search: WARN slow query 1.2s on report endpoint (single occurrence) (search, us-east; 94 min before the change; record R010)
