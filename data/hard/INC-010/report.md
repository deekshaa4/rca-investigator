# INC-010: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service catalog, region eu-west went from 0.003265 to 0.007381 (+126%) starting 2026-03-26T10:45:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 273 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment caused the error rate to increase.** (deployment, confidence 30%) [E5]
   - Why: The deployment of catalog v1.24 to eu-west led to a change in error rate.
   - Why: The deployment occurred 273 minutes before the error rate change.
   - Why: The error rate increased from 0.33% to 0.74% after the deployment.
   - Why: evidence_ids
2. **No clear evidence of a configuration change.** (unknown, confidence 30%) [E1, E2, E3, E4]
   - Why: No configuration changes were observed in the evidence.
   - Why: The error rate increase is not correlated with any configuration changes.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: The request volume and latency did not change significantly. [E3, E4]
- The increase in error rate was due to a failure of an upstream service.: No evidence of a failure or slowdown of an upstream service was found. [E1, E2, E3, E4]

## Actions
- (corrective, high) Roll back the deployment to catalog v1.24 to eu-west.
- (preventive, high) Monitor the system closely for any further changes and take corrective action if needed.
- (preventive, medium) Review and update the deployment process to include more rigorous testing and validation.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region eu-west rose from 0.33% to 0.74% (+126%), with a change point at 2026-03-26T10:45:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region eu-west stayed about the same (563 per 5 min before, 697 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region eu-west stayed about the same (120 ms before, 119 ms after, -0%).
- **E5** (record, deploys) Deployed catalog v1.24 to eu-west (catalog, eu-west; 273 min before the change; record R013)
