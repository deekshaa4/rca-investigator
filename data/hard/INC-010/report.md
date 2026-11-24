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
   - Why: The deployment occurred 273 minutes before the change in error rate.
   - Why: The error rate increased from 0.33% to 0.74% after the deployment.
   - Why: evidence_ids
2. **The deployment may have introduced a bug.** (unknown, confidence 30%) [E1, E2, E3, E4]
   - Why: The deployment of catalog v1.24 coincided with the increase in error rate.
   - Why: The error rate increased after the deployment, but the request volume and latency remained stable.
   - Why: There is no clear evidence of a bug in the deployment itself.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: The request volume and latency remained stable, indicating no sudden increase in user traffic. [E3, E4]
- The increase in error rate was due to a configuration change.: The deployment of catalog v1.24 was the only change in the system, and the error rate increased after the deployment. [E5]

## Actions
- (corrective, high) Roll back the deployment of catalog v1.24 to eu-west.
- (preventive, high) Implement automated monitoring for error rates and request volumes to detect anomalies early.
- (preventive, medium) Review and test the deployment of catalog v1.24 in a staging environment before production.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region eu-west rose from 0.33% to 0.74% (+126%), with a change point at 2026-03-26T10:45:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region eu-west stayed about the same (563 per 5 min before, 697 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region eu-west stayed about the same (120 ms before, 119 ms after, -0%).
- **E5** (record, deploys) Deployed catalog v1.24 to eu-west (catalog, eu-west; 273 min before the change; record R013)
