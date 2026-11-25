# INC-005: Why did the error rate go up on 20 March 2026?

## What changed
error_rate for service checkout, region eu-west went from 0.005316 to 0.01143 (+115%) starting 2026-03-20T09:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✓ A change event (deploys) lines up in time (1 min before the change).
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment of catalog v4.20 to us-east caused the error rate to rise in eu-west.** (deployment, confidence 30%) [E1, E2, E5]
   - Why: Deployed catalog v4.20 to us-east (record R014) caused the error rate to rise in eu-west (record E1).
   - Why: The error rate in eu-west increased from 0.53% to 1.14% (record E1).
   - Why: The error rate in eu-west was the only segment that changed (record E2).
   - Why: evidence_ids
2. **The increase in error rate is not due to a change in request volume or latency.** (unknown, confidence 30%) [E1, E3, E4]
   - Why: The error rate in eu-west increased from 0.53% to 1.14% (record E1).
   - Why: The request volume in eu-west stayed about the same (record E3).
   - Why: The p95 latency in eu-west stayed about the same (record E4).
   - Why: evidence_ids

## Ruled out
- The typo on the help page caused the error rate to rise.: Customer reports a typo on the help page (record R013) is not related to the error rate increase in eu-west (record E1). [E6]
- The customer asking how to download an invoice caused the error rate to rise.: Customer asks how to download an invoice (record R011) is not related to the error rate increase in eu-west (record E1). [E8]
- The routine release of checkout v3.20 to ap-south caused the error rate to rise in eu-west.: Routine release of checkout v3.20 to ap-south (record R012) is not related to the error rate increase in eu-west (record E1). [E7]

## Actions
- (corrective, high) Roll back the catalog v4.20 deployment to us-east.
- (preventive, medium) Monitor the error rate in eu-west for the next 24 hours and take further action if the error rate continues to rise.
- (preventive, medium) Review the deployment process for catalog v4.20 to ensure it does not cause similar issues in the future.

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.53% to 1.14% (+115%), with a change point at 2026-03-20T09:35:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (280 per 5 min before, 348 per 5 min after, +25%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (222 ms before, 223 ms after, +0%).
- **E5** (record, deploys) Deployed catalog v4.20 to us-east (catalog, us-east; 1 min before the change; record R014; fit: different service/region, so unlikely to be the cause)
- **E6** (record, tickets) Customer reports a typo on the help page. (catalog, us-east; 91 min before the change; record R013; fit: different service/region, so unlikely to be the cause)
- **E7** (record, deploys) Deployed checkout v3.20 to ap-south (routine release) (checkout, ap-south; 278 min before the change; record R012; fit: different service/region, so unlikely to be the cause)
- **E8** (record, tickets) Customer asks how to download an invoice. (auth, us-east; 340 min before the change; record R011; fit: different service/region, so unlikely to be the cause)
