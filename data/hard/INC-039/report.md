# INC-039: Why did the error rate go up on 16 March 2026?

## What changed
error_rate for service catalog went from 0.003604 to 0.04124 (+1044%) starting 2026-03-16T09:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 225 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region

## Possible leads (not confirmed)
1. **New deployment caused increased error rate and latency.** (deployment, confidence 30%) [E9, E1]
   - Why: Checkout v4.18 was deployed to us-east, which likely introduced the error.
   - Why: The deployment occurred 225 minutes before the error rate spike, suggesting it was the cause.
   - Why: The error rate and latency increased after the deployment, indicating the deployment was the root cause.

## Ruled out
- Increased traffic caused the error.: Request volume increased by 24%, but the error rate increased by 1044%, indicating a more significant issue. [E3]
- Configuration change caused the error.: No evidence directly links a configuration change to the error. []
- Data quality issues caused the error.: No evidence suggests the error was caused by bad input data. []
- Infrastructure issues caused the error.: No evidence suggests the error was caused by server, network, or capacity issues. []
- Unknown issue caused the error.: No other plausible explanations are supported by the evidence. []

## Actions
- (corrective, high) Rollback the checkout v4.18 deployment to us-east.
- (preventive, medium) Monitor catalog-db for any further issues and ensure it is performing optimally.
- (preventive, medium) Review and optimize the service catalog's error handling and retry mechanisms.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.36% to 4.12% (+1044%), with a change point at 2026-03-16T09:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.13).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1617 per 5 min before, 2010 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (121 ms before, 217 ms after, +80%).
- **E5** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, ap-south; 14 min after the change; record R011)
- **E6** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 20 min after the change; record R012)
- **E7** (record, tickets) catalog-db status page: investigating degraded performance (catalog; 30 min after the change; record R014)
- **E8** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 24 min after the change; record R013)
- **E9** (record, deploys) Deployed checkout v4.18 to us-east (routine release) (checkout, us-east; 225 min before the change; record R010)
