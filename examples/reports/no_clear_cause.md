# INC-005: Why did the error rate go up on 20 March 2026?

## What changed
error_rate for service checkout, region eu-west went from 0.005269 to 0.01133 (+115%) starting 2026-03-20T09:55:00Z. [E1, E2]

## Verdict: insufficient (score 0.37)
- ✗ The closest change event is 210 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The deployment of catalog v1.5 to us-east is the most likely cause of the error rate increase.** (deployment, confidence 30%) [E5, E1, E6]
   - Why: The deployment of catalog v1.5 to us-east occurred 360 minutes before the error rate increase.
   - Why: The error rate for service checkout in region eu-west increased after this deployment.
   - Why: No other deployments in the same region or time frame are known to have caused the error rate increase.
2. **The increase in request volume could be a contributing factor, but it is not the main cause.** (traffic, confidence 30%) [E3, E1]
   - Why: The request volume for service checkout in region eu-west increased by 24% after the deployment.
   - Why: The error rate increased by 115% after the deployment.
   - Why: The increase in request volume is not significantly higher than the increase in error rate.

## Ruled out
- The traffic increase is the main cause.: The error rate increase is more significant than the request volume increase. [E3]
- The configuration change is the main cause.: No configuration changes are listed in the evidence. []
- The dependency issue is the main cause.: No evidence points to an external service failure or slowdown. []
- The infrastructure issue is the main cause.: No evidence points to any issues with the infrastructure. []
- The data issue is the main cause.: No evidence points to bad or unusual input data. []
- The unknown issue is the main cause.: No other plausible causes are ruled out. []

## Actions
- (corrective, high) Roll back the catalog v1.5 deployment to us-east to see if the error rate decreases.
- (preventive, medium) Monitor the error rate and request volume for service checkout in region eu-west for any further increases or changes.
- (preventive, medium) Review the catalog v1.5 deployment for any potential issues and improve the deployment process to catch such issues early.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.53% to 1.13% (+115%), with a change point at 2026-03-20T09:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.11).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (281 per 5 min before, 348 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (221 ms before, 222 ms after, +1%).
- **E5** (record, deploys) Deployed checkout v2.14 to us-east (routine release) (checkout, us-east; 210 min before the change; record R010)
- **E6** (record, deploys) Deployed search v3.19 to us-east (routine release) (search, us-east; 283 min before the change; record R009)
- **E7** (record, deploys) Deployed catalog v2.22 to ap-south (routine release) (catalog, ap-south; 345 min before the change; record R008)
- **E8** (record, deploys) Deployed catalog v1.5 to us-east (routine release) (catalog, us-east; 360 min before the change; record R007)
