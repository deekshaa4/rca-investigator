# INC-006: Why did the error rate go up on 20 March 2026?

## What changed
error_rate for service catalog, region eu-west went from 0.004027 to 0.03336 (+729%) starting 2026-03-20T04:45:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (1 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of catalog v4.0 introduced a NullPointerException.** (deployment, confidence 90%) [E5, E8]
   - Why: The error rate increased after the deployment of catalog v4.0.
   - Why: The NullPointerException in RequestHandler.serialize (v4.0) caused the error.
   - Why: The error occurred 1 minute after the deployment, indicating the change was the cause.
2. **The deployment of catalog v4.0 was not followed by a routine release.** (unknown, confidence 80%) [E5, E7]
   - Why: The error rate increased after the deployment of catalog v4.0.
   - Why: There was no routine release of catalog v4.0, which could have mitigated the issue.
   - Why: The error occurred 1 minute after the deployment, indicating the change was the cause.
3. **The error rate increase is localized to the service catalog in region eu-west.** (unknown, confidence 70%) [E2]
   - Why: The error rate increase is concentrated in the service catalog in region eu-west.
   - Why: The error rate increase is not seen in other service/region segments.
   - Why: The error rate increase is localized to the service catalog in region eu-west.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The increase in error rate is due to a configuration change.: The deployment of catalog v4.0 was the only change made to the service catalog in region eu-west. [E5]

## Actions
- (corrective, high) Roll back the deployment of catalog v4.0 to eu-west.
- (preventive, high) Implement a more robust error handling mechanism in RequestHandler.serialize.
- (preventive, medium) Schedule routine releases for the service catalog in region eu-west.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region eu-west rose from 0.40% to 3.34% (+729%), with a change point at 2026-03-20T04:45:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region eu-west stayed about the same (567 per 5 min before, 647 per 5 min after, +14%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region eu-west stayed about the same (120 ms before, 121 ms after, +1%).
- **E5** (record, deploys) Deployed catalog v4.0 to eu-west (catalog, eu-west; 1 min before the change; record R015)
- **E6** (record, alerts) High error rate on catalog in eu-west (catalog, eu-west; 10 min after the change; record R018)
- **E7** (record, deploys) Deployed catalog v3.10 to eu-west (routine release) (catalog, eu-west; 98 min before the change; record R014)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.0) (catalog, eu-west; 1 min after the change; record R016)
- **E9** (record, deploys) Deployed catalog v2.24 to eu-west (catalog, eu-west; 206 min before the change; record R012)
