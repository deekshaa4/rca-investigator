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
1. **New version deployment caused the error rate spike.** (deployment, confidence 90%) [E5, E1]
   - Why: The deployment of auth v2.27 to ap-south led to the error rate increase.
   - Why: The error rate for service auth in region ap-south rose from 0.49% to 4.43%.
   - Why: The deployment occurred 2 minutes before the change point.
2. **Feature flag change may have contributed to the error rate increase.** (config_change, confidence 80%) [E6, E1]
   - Why: The change of auth feature flag new_ui_flow to 50% in ap-south may have introduced instability.
   - Why: The error rate increase coincided with the change of the feature flag.
   - Why: The feature flag change occurred 3 minutes before the change point.

## Ruled out
- Increased request volume caused the error rate increase.: The request volume for service auth in region ap-south stayed about the same. [E3]
- Latency increase caused the error rate increase.: The p95 latency for service auth in region ap-south stayed about the same. [E4]
- External dependency failure caused the error rate increase.: No evidence found that points to an external dependency failure. []

## Actions
- (corrective, high) Roll back the auth v2.27 deployment to ap-south.
- (preventive, high) Review and potentially revert the auth feature flag change to 50%.
- (preventive, medium) Monitor the system for any new deployments or config changes in the next 24 hours.

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
