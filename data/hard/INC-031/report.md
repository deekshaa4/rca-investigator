# INC-031: Why did the error rate go up on 03 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.004509 to 0.02494 (+453%) starting 2026-03-03T09:50:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **A new deployment of catalog v4.7 caused the error rate to spike.** (deployment, confidence 90%) [E5, E8, E9]
   - Why: v4.7 deployment introduced a new version of the RequestHandler that caused NullPointerExceptions.
   - Why: NullPointerExceptions led to a high error rate in the catalog service.
   - Why: The error rate increased from 0.45% to 2.49% within 21 minutes of the deployment.
   - Why: evidence_ids

## Ruled out
- The error rate increase was due to a sudden increase in user traffic.: The request volume remained stable before and after the error rate increase. [E3]
- The error rate increase was due to a sudden change in latency.: The p95 latency remained stable before and after the error rate increase. [E4]
- The error rate increase is not due to a sudden surge in requests.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E3]
- The error rate increase is not due to a sudden change in latency.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E4]

## Actions
- (corrective, high) Roll back the v4.7 deployment to prevent further error rate increase.
- (preventive, high) Monitor the RequestHandler for potential issues before deploying new versions.
- (preventive, medium) Investigate the root cause of the NullPointerExceptions in RequestHandler.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.45% to 2.49% (+453%), with a change point at 2026-03-03T09:50:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.13).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (727 per 5 min before, 904 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (121 ms before, 120 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v4.7 to us-east (catalog, us-east; 2 min before the change; record R013; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E7** (record, deploys) Deployed catalog v5.11 to us-east (catalog, us-east; 212 min before the change; record R012; fit: hours before the change, too early to explain a sudden jump)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.7) (catalog, us-east; 21 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v4.7) (catalog, us-east; 26 min after the change; record R016; fit: after the change, so a symptom, not a cause)
