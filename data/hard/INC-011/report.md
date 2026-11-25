# INC-011: Why did the error rate go up on 04 March 2026?

## What changed
error_rate for service auth, region eu-west went from 0.005099 to 0.03231 (+534%) starting 2026-03-04T08:50:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **The error rate spike coincides with a high error rate alert.** (unknown, confidence 30%) [E5, E9]
   - Why: The error rate spike is also reflected in a high error rate alert.
   - Why: This alert suggests that the error rate increase is a known issue, not a new problem.
   - Why: The alert occurred 10 minutes before the change, indicating a possible correlation.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The error rate increase is due to a configuration change.: There is no evidence of a configuration change that would cause the error rate to spike. [E1, E2, E3, E4]

## Actions
- (corrective, high) Roll back the deployment of the new version of the RequestHandler.
- (preventive, medium) Monitor the service for any new errors and alert on any significant changes in error rate.
- (preventive, high) Review the new version of the RequestHandler for potential issues and ensure proper testing before deployment.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region eu-west rose from 0.51% to 3.23% (+534%), with a change point at 2026-03-04T08:50:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.10).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region eu-west stayed about the same (373 per 5 min before, 460 per 5 min after, +23%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region eu-west stayed about the same (90 ms before, 91 ms after, +2%).
- **E5** (record, alerts) High error rate on auth in eu-west (auth, eu-west; 10 min after the change; record R013)
- **E6** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v5.21) (auth, eu-west; 16 min after the change; record R014)
- **E7** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v5.21) (auth, eu-west; 20 min after the change; record R015)
- **E8** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v5.21) (auth, eu-west; 27 min after the change; record R016)
- **E9** (record, logs) checkout: INFO autoscaler: no change (checkout, eu-west; 110 min before the change; record R012)
