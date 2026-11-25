# INC-005: Why did the error rate go up on 20 March 2026?

## What changed
error_rate for service checkout, region eu-west went from 0.005316 to 0.01143 (+115%) starting 2026-03-20T09:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 91 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New deployment of catalog v4.20 to us-east caused the error rate to increase.** (deployment, confidence 30%) [E1, E2, E3, E4, E6, E7, E8]
   - Why: Deployed catalog v4.20 to us-east (record R014) before the error rate spike.
   - Why: The error rate for service checkout in region eu-west increased from 0.53% to 1.14% (evidence E1).
   - Why: The error rate increase is concentrated in service checkout in region eu-west (evidence E2).
   - Why: The request volume for service checkout in region eu-west stayed about the same (evidence E3).
   - Why: The p95 latency for service checkout in region eu-west stayed about the same (evidence E4).

## Ruled out
- The error rate increase is due to a typo on the help page.: The error rate increase is not explained by the typo (evidence E6). [E6]
- The error rate increase is due to a customer asking how to download an invoice.: The error rate increase is not explained by the customer asking how to download an invoice (evidence E8). [E8]
- The error rate increase is due to a routine release of checkout v3.20 to ap-south.: The error rate increase is not explained by the routine release (evidence E7). [E7]

## Actions
- (corrective, high) Roll back the catalog v4.20 deployment to us-east.
- (preventive, high) Monitor the error rate for service checkout in region eu-west closely and take corrective action if the error rate increases again.
- (preventive, medium) Review and test the new catalog v4.20 thoroughly before deploying to other regions.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 1
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region eu-west rose from 0.53% to 1.14% (+115%), with a change point at 2026-03-20T09:35:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.12).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region eu-west stayed about the same (280 per 5 min before, 348 per 5 min after, +25%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region eu-west stayed about the same (222 ms before, 223 ms after, +0%).
- **E5** (record, deploys) Deployed catalog v4.20 to us-east (catalog, us-east; 1 min before the change; record R014)
- **E6** (record, tickets) Customer reports a typo on the help page. (catalog, us-east; 91 min before the change; record R013)
- **E7** (record, deploys) Deployed checkout v3.20 to ap-south (routine release) (checkout, ap-south; 278 min before the change; record R012)
- **E8** (record, tickets) Customer asks how to download an invoice. (auth, us-east; 340 min before the change; record R011)
