# INC-015: Why did the error rate go up on 15 March 2026?

## What changed
error_rate for service search, region us-east went from 0.004841 to 0.01119 (+131%) starting 2026-03-15T04:10:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✓ A change event (deploys) lines up in time (4 min before the change).
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The deployment of catalog v4.12 to ap-south caused the error rate to increase.** (deployment, confidence 30%) [E5, E1]
   - Why: The deployment of catalog v4.12 to ap-south introduced a new version of the catalog.
   - Why: The new version of the catalog was not fully tested and caused errors in the service search in region us-east.
   - Why: The error rate increased from 0.48% to 1.12% after the deployment.
2. **The deployment of catalog v2.24 to eu-west did not cause the error rate to increase.** (unknown, confidence 30%) [E6, E1]
   - Why: The deployment of catalog v2.24 to eu-west was a routine release and did not affect the error rate in us-east.
   - Why: The error rate increase was specific to the us-east region and the service search.
   - Why: The error rate in other regions and services remained stable.

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The increase in error rate was due to a configuration change in the service search.: The deployment of catalog v4.12 was the only change in the system. [E5, E1]

## Actions
- (corrective, high) Roll back the deployment of catalog v4.12 to ap-south.
- (preventive, high) Implement comprehensive testing for new catalog versions before deployment.
- (preventive, medium) Monitor the error rate and request volume in the us-east region closely.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region us-east rose from 0.48% to 1.12% (+131%), with a change point at 2026-03-15T04:10:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.11).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region us-east stayed about the same (1114 per 5 min before, 1250 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region us-east stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v4.12 to ap-south (catalog, ap-south; 4 min before the change; record R007)
- **E6** (record, deploys) Deployed catalog v2.24 to eu-west (routine release) (catalog, eu-west; 166 min before the change; record R006)
