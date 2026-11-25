# INC-035: Why did the error rate go up on 25 March 2026?

## What changed
error_rate for service checkout, region ap-south went from 0.003675 to 0.008217 (+124%) starting 2026-03-25T02:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 211 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment caused the error rate to increase.** (deployment, confidence 30%) [E5]
   - Why: Checkout v8.9 was deployed to ap-south 211 minutes before the error rate increase.
   - Why: The error rate for service checkout in region ap-south increased from 0.37% to 0.82%.
   - Why: The deployment of checkout v8.9 is the most likely cause of the error rate increase.

## Ruled out
- The increase in error rate was due to a sudden increase in request volume.: The request volume for service checkout in region ap-south stayed about the same before and after the change. [E3]
- The increase in error rate was due to a change in latency.: The p95 latency for service checkout in region ap-south stayed about the same before and after the change. [E4]

## Actions
- (corrective, high) Rollback the deployment of checkout v8.9 to ap-south.
- (preventive, high) Monitor the system for any further issues and prepare for a quick rollback if necessary.
- (preventive, medium) Investigate the deployment of checkout v8.9 to identify and address any issues.

## Fact-check
- Evidence IDs cited by the model: 3, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region ap-south rose from 0.37% to 0.82% (+124%), with a change point at 2026-03-25T02:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.11).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region ap-south stayed about the same (175 per 5 min before, 187 per 5 min after, +7%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region ap-south stayed about the same (221 ms before, 221 ms after, -0%).
- **E5** (record, deploys) Deployed checkout v8.9 to ap-south (checkout, ap-south; 211 min before the change; record R010)
