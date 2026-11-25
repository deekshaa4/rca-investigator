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
1. **The error rate increase is likely due to a configuration change in the service.** (config_change, confidence 30%) [E1, E2, E5, E6]
   - Why: The error rate increased after a deployment to ap-south, which is a configuration change.
   - Why: The deployment to ap-south happened 34 minutes after the error rate increase, which is right time and place.
   - Why: The error rate in the eu-west region, where the service is located, increased after the deployment to ap-south.
   - Why: evidence_ids
2. **The increase in error rate could also be due to a change in the service itself.** (unknown, confidence 30%) [E1, E2, E5, E6]
   - Why: The error rate increased after a deployment to ap-south, which is a configuration change.
   - Why: The deployment to ap-south happened 34 minutes after the error rate increase, which is right time and place.
   - Why: The error rate in the eu-west region, where the service is located, increased after the deployment to ap-south.
   - Why: evidence_ids

## Ruled out
- The increase in error rate could be due to a change in the catalog service.: The catalog service is deployed to ap-south, but the error rate increase is in the eu-west region. [E6]
- The increase in error rate could be due to a change in the auth service.: The auth service is deployed to ap-south, but the error rate increase is in the eu-west region. [E5]

## Actions
- (corrective, high) Review and validate the configuration changes made in ap-south.
- (preventive, high) Monitor the eu-west region for any further error rate increases and take appropriate action.
- (preventive, medium) Review the deployment process to ensure that changes are properly scoped and tested.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.52% to 1.08% (+109%), with a change point at 2026-03-20T02:40:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.09).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (289 per 5 min before, 312 per 5 min after, +8%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (219 ms before, 222 ms after, +1%).
- **E5** (record, deploys) Deployed auth v4.12 to ap-south (routine release) (auth, ap-south; 146 min before the change; record R005; fit: different service/region, so unlikely to be the cause)
- **E6** (record, deploys) Deployed catalog v8.27 to ap-south (catalog, ap-south; 34 min after the change; record R006; fit: after the change, so a symptom, not a cause)
