# INC-041: Why did the error rate go up on 07 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.00374 to 0.02044 (+446%) starting 2026-03-07T05:25:00Z. [E1, E2]

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
1. **New UI flow feature flag change introduced a bug in the catalog service.** (config_change, confidence 90%) [E5, E6, E1, E8, E9]
   - Why: The new UI flow feature flag was changed to 50% (record R011).
   - Why: This change was made 3 minutes before the error rate spike (record R011).
   - Why: The error rate in the catalog service increased sharply (record E1).
   - Why: The error occurred in the RequestHandler.serialize method of version v3.14 (record E8 and E9).
   - Why: The error was a NullPointerException (record E8 and E9).
2. **The deployment of catalog v3.14 introduced the bug.** (deployment, confidence 80%) [E5, E1, E8, E9]
   - Why: The catalog v3.14 deployment was made 2 minutes before the error rate spike (record R012).
   - Why: The error rate in the catalog service increased sharply (record E1).
   - Why: The error occurred in the RequestHandler.serialize method of version v3.14 (record E8 and E9).
   - Why: The error was a NullPointerException (record E8 and E9).

## Ruled out
- The increase in request volume caused the error.: The request volume did not change significantly (record E3). [E3]
- The increase in latency caused the error.: The p95 latency did not change significantly (record E4). [E4]
- The error was due to external service failure.: No external service failure was reported (no evidence of external service issues). []

## Actions
- (corrective, high) Roll back the catalog v3.14 deployment to prevent further errors.
- (preventive, medium) Implement a more robust error handling mechanism in the RequestHandler.serialize method.
- (preventive, medium) Monitor the new UI flow feature flag changes more closely and implement a rollback mechanism for such changes.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.37% to 2.04% (+446%), with a change point at 2026-03-07T05:25:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (735 per 5 min before, 852 per 5 min after, +16%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (121 ms before, 120 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v3.14 to us-east (catalog, us-east; 2 min before the change; record R012)
- **E6** (record, config_changes) Changed catalog feature flag new_ui_flow to 50% in us-east (catalog, us-east; 3 min before the change; record R011)
- **E7** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R015)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.14) (catalog, us-east; 3 min after the change; record R013)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.14) (catalog, us-east; 8 min after the change; record R014)
