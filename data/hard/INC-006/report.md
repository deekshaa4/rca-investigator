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
1. **New deployment of catalog v4.0 caused the error rate to spike.** (deployment, confidence 90%) [E5, E8]
   - Why: catalog v4.0 deployment introduced a new version of the RequestHandler.serialize function, which caused a NullPointerException.
   - Why: NullPointerException in RequestHandler.serialize (v4.0) was observed 1 minute after the deployment.
   - Why: The error rate increased from 0.40% to 3.34% after the deployment, indicating the deployment was the cause.

## Ruled out
- The error rate increase was due to a sudden increase in request volume or latency.: Request volume and latency remained stable before and after the error rate increase. [E3, E4]
- The error rate increase was due to a routine release of catalog v3.10.: Routine release of catalog v3.10 did not cause the error rate increase. [E7]
- The error rate increase was not due to a routine release of catalog v3.10.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E7]
- The error rate increase was not due to a sudden increase in request volume or latency.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3, E4]

## Actions
- (corrective, high) Roll back the catalog v4.0 deployment to prevent further error rate increase.
- (preventive, medium) Implement a robust error handling mechanism in the RequestHandler.serialize function to prevent NullPointerExceptions.
- (preventive, medium) Monitor the RequestHandler.serialize function for any other potential issues that may cause NullPointerExceptions.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region eu-west rose from 0.40% to 3.34% (+729%), with a change point at 2026-03-20T04:45:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region eu-west stayed about the same (567 per 5 min before, 647 per 5 min after, +14%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region eu-west stayed about the same (120 ms before, 121 ms after, +1%).
- **E5** (record, deploys) Deployed catalog v4.0 to eu-west (catalog, eu-west; 1 min before the change; record R015; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on catalog in eu-west (catalog, eu-west; 10 min after the change; record R018; fit: after the change, so a symptom, not a cause)
- **E7** (record, deploys) Deployed catalog v3.10 to eu-west (routine release) (catalog, eu-west; 98 min before the change; record R014; fit: hours before the change, too early to explain a sudden jump)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.0) (catalog, eu-west; 1 min after the change; record R016; fit: describes a symptom, not a change)
- **E9** (record, deploys) Deployed catalog v2.24 to eu-west (catalog, eu-west; 206 min before the change; record R012; fit: hours before the change, too early to explain a sudden jump)
