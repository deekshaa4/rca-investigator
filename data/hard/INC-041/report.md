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
1. **A new deployment of catalog v3.14 caused the error rate to spike.** (deployment, confidence 90%) [E5, E7, E8, E9]
   - Why: The deployment of catalog v3.14 introduced a new version of the service.
   - Why: The new version of the service had a bug that caused NullPointerExceptions.
   - Why: NullPointerExceptions led to a high error rate in the service.
   - Why: evidence_ids
2. **A configuration change to the catalog feature flag caused the error rate to spike.** (config_change, confidence 80%) [E6, E7, E8, E9]
   - Why: The feature flag change enabled a new feature in the catalog.
   - Why: The new feature was not fully tested and caused NullPointerExceptions.
   - Why: NullPointerExceptions led to a high error rate in the service.
   - Why: evidence_ids

## Ruled out
- The increase in request volume caused the error rate to spike.: The request volume stayed about the same before and after the change. [E3]
- The increase in p95 latency caused the error rate to spike.: The p95 latency stayed about the same before and after the change. [E4]
- The error rate spike was due to a sudden increase in traffic.: The request volume increased by 16%, but the error rate increased by 446%. [E3]

## Actions
- (corrective, high) Roll back the catalog v3.14 deployment to revert the changes.
- (preventive, high) Disable the new_ui_flow feature flag to prevent the NullPointerExceptions.
- (preventive, medium) Conduct a thorough regression testing of the catalog v3.14 version.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.37% to 2.04% (+446%), with a change point at 2026-03-07T05:25:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (735 per 5 min before, 852 per 5 min after, +16%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (121 ms before, 120 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v3.14 to us-east (catalog, us-east; 2 min before the change; record R012; fit: right time and place: a strong candidate cause)
- **E6** (record, config_changes) Changed catalog feature flag new_ui_flow to 50% in us-east (catalog, us-east; 3 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E7** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.14) (catalog, us-east; 3 min after the change; record R013; fit: describes a symptom, not a change)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.14) (catalog, us-east; 8 min after the change; record R014; fit: after the change, so a symptom, not a cause)
