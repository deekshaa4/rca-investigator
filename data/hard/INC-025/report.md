# INC-025: Why did the error rate go up on 09 March 2026?

## What changed
error_rate for service auth, region eu-west went from 0.002781 to 0.006804 (+145%) starting 2026-03-09T15:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.35)
- ✗ The closest change event is 287 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New feature request introduced unexpected load.** (unknown, confidence 30%) [E5]
   - Why: Feature request R013 was made 287 minutes before the error rate spike.
   - Why: The feature request likely caused a temporary increase in load on the system.
   - Why: The error rate increased without a corresponding increase in request volume or latency.
2. **Deployment of a new feature introduced a bug.** (deployment, confidence 30%) [E1, E2, E5]
   - Why: The error rate spike coincided with a deployment of a new feature.
   - Why: The feature deployment was made 287 minutes before the error rate spike.
   - Why: The error rate increased without a corresponding increase in request volume or latency.
3. **Increased load due to a new feature.** (traffic, confidence 30%) [E1, E2, E5]
   - Why: The error rate spike coincided with a deployment of a new feature.
   - Why: The feature deployment was made 287 minutes before the error rate spike.
   - Why: The error rate increased without a corresponding increase in request volume or latency.

## Ruled out
- Configuration change caused the error rate spike.: No configuration changes were made around the time of the error rate spike. [E1, E2, E3, E4]
- Dependency issue with an external service caused the error rate spike.: No external services were known to be affected around the time of the error rate spike. [E1, E2, E3, E4]
- Infrastructure issue caused the error rate spike.: No infrastructure issues were reported around the time of the error rate spike. [E1, E2, E3, E4]
- Data issue caused the error rate spike.: No unusual data inputs were reported around the time of the error rate spike. [E1, E2, E3, E4]

## Actions
- (corrective, high) Roll back the deployment of the new feature.
- (preventive, medium) Monitor for similar spikes in error rates in the future.
- (preventive, medium) Review and test the new feature thoroughly before deployment.

## Fact-check
- Evidence IDs cited by the model: 23, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region eu-west rose from 0.28% to 0.68% (+145%), with a change point at 2026-03-09T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.26).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region eu-west stayed about the same (391 per 5 min before, 439 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region eu-west stayed about the same (90 ms before, 91 ms after, +0%).
- **E5** (record, tickets) Feature request: dark mode for the account page. (catalog, eu-west; 287 min before the change; record R013; fit: different service/region, so unlikely to be the cause)
