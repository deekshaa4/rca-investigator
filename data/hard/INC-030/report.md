# INC-030: Why did the error rate go up on 20 March 2026?

## What changed
error_rate for service checkout, region eu-west went from 0.005187 to 0.01084 (+109%) starting 2026-03-20T02:40:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 146 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The deployment of auth v4.12 to ap-south likely caused the increase in error rate.** (deployment, confidence 30%) [E5, E1]
   - Why: auth v4.12 deployment to ap-south introduced a new version of the service.
   - Why: The new version of auth v4.12 was deployed to ap-south 146 minutes before the error rate increase.
   - Why: The error rate for service checkout in region eu-west increased from 0.52% to 1.08% after the deployment.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a change in configuration settings.: No evidence of a configuration change that could have caused the error rate increase. [E3, E4]
- The increase in error rate was due to a change in traffic patterns.: The request volume and p95 latency for service checkout in region eu-west did not change significantly. [E3, E4]
- The increase in error rate was due to a failure of an external service.: No evidence of a failure of an external service that could have caused the error rate increase. [E3, E4]

## Actions
- (corrective, high) Roll back the auth v4.12 deployment to ap-south.
- (preventive, medium) Monitor the error rate for service checkout in region eu-west for any further increases and investigate the cause.
- (preventive, medium) Monitor the error rate for service checkout in region eu-west for any further increases and investigate the cause.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.52% to 1.08% (+109%), with a change point at 2026-03-20T02:40:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.09).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (289 per 5 min before, 312 per 5 min after, +8%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (219 ms before, 222 ms after, +1%).
- **E5** (record, deploys) Deployed auth v4.12 to ap-south (routine release) (auth, ap-south; 146 min before the change; record R005)
- **E6** (record, deploys) Deployed catalog v8.27 to ap-south (catalog, ap-south; 34 min after the change; record R006)
