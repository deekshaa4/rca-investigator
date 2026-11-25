# INC-016: Why did the error rate go up on 07 March 2026?

## What changed
error_rate for service auth, region ap-south went from 0.004888 to 0.04434 (+807%) starting 2026-03-07T07:10:00Z. [E1, E2]

## Verdict: partial (score 0.90)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The deployment of auth v2.27 to ap-south likely caused the increase in error rate.** (deployment, confidence 90%) [E5, E1]
   - Why: The deployment of auth v2.27 to ap-south introduced a new version of the service.
   - Why: The new version (v2.27) was deployed 2 minutes before the error rate spike.
   - Why: The error rate increased significantly (from 0.49% to 4.43%) after the deployment.
2. **The change in the auth feature flag to 50% in ap-south may have contributed to the error rate increase.** (config_change, confidence 80%) [E6, E1]
   - Why: The feature flag change occurred 3 minutes before the error rate spike.
   - Why: The feature flag change to 50% may have altered the service's behavior or performance.
   - Why: The error rate spiked after the feature flag change.

## Ruled out
- The increase in request volume caused the error rate to rise.: The request volume remained about the same before and after the change. [E3]
- The change in p95 latency caused the error rate to rise.: The p95 latency remained about the same before and after the change. [E4]

## Actions
- (corrective, high) Roll back the deployment of auth v2.27 to ap-south.
- (preventive, high) Review and potentially revert the change in the auth feature flag to 50% in ap-south.
- (preventive, medium) Monitor the error rate and request volume closely for any further spikes.

## Fact-check
- Evidence IDs cited by the model: 6, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region ap-south rose from 0.49% to 4.43% (+807%), with a change point at 2026-03-07T07:10:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.10).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region ap-south stayed about the same (223 per 5 min before, 271 per 5 min after, +21%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region ap-south stayed about the same (91 ms before, 89 ms after, -1%).
- **E5** (record, deploys) Deployed auth v2.27 to ap-south (auth, ap-south; 2 min before the change; record R014)
- **E6** (record, config_changes) Changed auth feature flag new_ui_flow to 50% in ap-south (auth, ap-south; 3 min before the change; record R013)
- **E7** (record, alerts) High error rate on auth in ap-south (auth, ap-south; 10 min after the change; record R015)
- **E8** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.27) (auth, ap-south; 19 min after the change; record R016)
- **E9** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.27) (auth, ap-south; 28 min after the change; record R017)
