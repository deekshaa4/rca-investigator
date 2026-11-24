# INC-026: Why did the error rate go up on 04 March 2026?

## What changed
error_rate for service auth, region us-east went from 0.003785 to 0.03709 (+880%) starting 2026-03-04T04:55:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (8 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of auth v2.14 caused the error rate to spike.** (deployment, confidence 90%) [E5, E7, E8]
   - Why: auth v2.14 deployment introduced a new error (NullPointerException) in RequestHandler.serialize.
   - Why: This error led to a high error rate in service auth in region us-east.
   - Why: The error rate increase coincided with the deployment of auth v2.14.
2. **The deployment of auth v2.14 was not properly tested.** (unknown, confidence 80%) [E5, E7, E8]
   - Why: The error occurred in the new deployment of auth v2.14.
   - Why: The error was not caught during the deployment process.
   - Why: The error led to a high error rate in service auth in region us-east.

## Ruled out
- The increase in error rate was due to increased traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The error rate increase was due to a configuration change.: No evidence of a configuration change was found. [E1, E2, E3, E4]
- The error rate increase was due to a dependency issue with another service.: No evidence of a dependency issue was found. [E1, E2, E3, E4]
- The error rate increase was due to infrastructure issues.: No evidence of infrastructure issues was found. [E1, E2, E3, E4]

## Actions
- (corrective, high) Roll back the auth v2.14 deployment to us-east.
- (preventive, high) Implement a thorough testing process for new deployments.
- (preventive, medium) Review and improve the error handling and logging mechanisms in RequestHandler.serialize.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region us-east rose from 0.38% to 3.71% (+880%), with a change point at 2026-03-04T04:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region us-east stayed about the same (490 per 5 min before, 564 per 5 min after, +15%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region us-east stayed about the same (90 ms before, 90 ms after, -0%).
- **E5** (record, deploys) Deployed auth v2.14 to us-east (auth, us-east; 8 min before the change; record R010)
- **E6** (record, alerts) High error rate on auth in us-east (auth, us-east; 5 min after the change; record R012)
- **E7** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.14) (auth, us-east; 3 min after the change; record R011)
- **E8** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.14) (auth, us-east; 22 min after the change; record R013)
- **E9** (record, deploys) Deployed search v8.0 to eu-west (search, eu-west; 9 min before the change; record R009)
