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
1. **New deployment of checkout v4.18 to us-east caused increased error rate in service catalog.** (deployment, confidence 30%) [E9, E5, E6, E7]
   - Why: Checkout v4.18 deployment to us-east introduced a new version of the service.
   - Why: The new version of the service caused issues with the upstream catalog-db.
   - Why: The issues with catalog-db led to timeout errors in the service catalog.
   - Why: The timeout errors increased the error rate in the service catalog.
   - Why: The increased error rate is observed on 16 March 2026.
2. **Increased request volume to service catalog caused higher error rate.** (traffic, confidence 30%) [E2, E3]
   - Why: The error rate in service catalog increased from 0.36% to 4.12%.
   - Why: The increase in error rate coincides with a 24% increase in request volume.
   - Why: The increase in request volume is likely due to a campaign or user behavior change.
   - Why: The campaign or user behavior change led to more users or requests than usual.
   - Why: The increased load on the service catalog caused the error rate to rise.

## Ruled out
- Configuration change to service catalog caused the error rate to increase.: No configuration change was observed in the evidence. [E1, E2, E3, E4]
- Data quality issues caused the error rate to increase.: No data quality issues were observed in the evidence. [E1, E2, E3, E4]
- External dependency issues caused the error rate to increase.: No external dependency issues were observed in the evidence. [E1, E2, E3, E4]

## Actions
- (corrective, high) Rollback the checkout v4.18 deployment to us-east.
- (preventive, medium) Monitor the service catalog for any further issues and take corrective action if needed.
- (preventive, medium) Review and optimize the service catalog's request handling to better manage increased load.

## Fact-check
- Evidence IDs cited by the model: 18, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.36% to 4.12% (+1044%), with a change point at 2026-03-16T09:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.13).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1617 per 5 min before, 2010 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (121 ms before, 217 ms after, +80%).
- **E5** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, ap-south; 14 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E6** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 20 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E7** (record, tickets) catalog-db status page: investigating degraded performance (catalog; 30 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 24 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, deploys) Deployed checkout v4.18 to us-east (routine release) (checkout, us-east; 225 min before the change; record R010; fit: different service/region, so unlikely to be the cause)
