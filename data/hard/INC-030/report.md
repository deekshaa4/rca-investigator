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
1. **The deployment of auth v4.12 to ap-south may have caused the increase in error rate.** (deployment, confidence 30%) [E5, E1]
   - Why: The deployment of auth v4.12 to ap-south introduced a new version of the authentication service.
   - Why: This new version of the authentication service may have introduced bugs or incompatibilities.
   - Why: These bugs or incompatibilities could have affected the service checkout in region eu-west, leading to an increase in error rate.

## Ruled out
- The increase in error rate was due to a change in the configuration of the service checkout in region eu-west.: The error rate and request volume remained relatively stable, indicating no significant configuration changes. [E2, E3]
- The increase in error rate was due to a change in the traffic patterns of the service checkout in region eu-west.: The request volume and latency remained relatively stable, indicating no significant changes in traffic patterns. [E2, E3]

## Actions
- (corrective, high) Roll back the deployment of catalog v8.27 to ap-south to investigate the root cause and prevent further issues.
- (preventive, medium) Monitor the error rate and request volume for the service checkout in region eu-west closely after the deployment of auth v4.12 to ap-south.
- (preventive, medium) Review and test the new version of the authentication service (auth v4.12) in a staging environment before deploying it to production.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.52% to 1.08% (+109%), with a change point at 2026-03-20T02:40:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.09).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (289 per 5 min before, 312 per 5 min after, +8%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (219 ms before, 222 ms after, +1%).
- **E5** (record, deploys) Deployed auth v4.12 to ap-south (routine release) (auth, ap-south; 146 min before the change; record R005)
- **E6** (record, deploys) Deployed catalog v8.27 to ap-south (catalog, ap-south; 34 min after the change; record R006)
