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
   - Why: Checkout v4.18 deployment introduced changes that affected service catalog.
   - Why: Changes in service catalog led to an increase in error rate and latency.
   - Why: Increased error rate and latency are observed in service catalog metrics.

## Ruled out
- User traffic increase caused the error rate increase.: Request volume for service catalog did not change significantly. [E3]
- Configuration change caused the error rate increase.: No evidence of configuration changes that affected service catalog. []
- Infrastructure issue caused the error rate increase.: No evidence of infrastructure issues affecting service catalog. []
- Data quality issues caused the error rate increase.: No evidence of bad or unusual input data affecting service catalog. []

## Actions
- (corrective, high) Implement a retry mechanism for catalog-db timeout errors.
- (preventive, high) Monitor catalog-db performance closely and take immediate action if degraded performance is detected.
- (preventive, medium) Review and test the checkout v4.18 release for any potential issues.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

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
