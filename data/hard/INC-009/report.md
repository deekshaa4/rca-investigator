# INC-009: Why did the error rate go up on 21 March 2026?

## What changed
error_rate for service catalog went from 0.004151 to 0.05466 (+1217%) starting 2026-03-21T15:30:00Z. [E1, E2]

## Verdict: sufficient (score 0.93)
- ✓ A change event (alerts) lines up in time (2 min after the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The deployment of catalog v3.27 to eu-west caused the error rate to rise.** (deployment, confidence 90%) [E8, E5, E6, E7]
   - Why: The deployment of catalog v3.27 introduced a new version of the service.
   - Why: The new version of the service interacted with the upstream catalog-db, causing it to return HTTP 503.
   - Why: The catalog-db timeout retries caused the service to experience increased latency and error rates.
2. **The catalog-db is experiencing degraded performance, which is affecting the service catalog.** (dependency, confidence 80%) [E5, E6, E7]
   - Why: The catalog-db is an upstream service used by the service catalog.
   - Why: The catalog-db is experiencing degraded performance, indicated by the HTTP 503 status.
   - Why: The degraded performance of the catalog-db is causing the service catalog to experience increased latency and error rates.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume for service catalog did not change significantly. [E3]
- The increase in error rate is due to a configuration change in the service catalog.: The error rate change is concentrated in the service catalog, not in other service/region segments. [E2]

## Actions
- (corrective, high) Roll back the catalog v3.27 deployment to eu-west.
- (preventive, medium) Monitor the catalog-db for any further issues and ensure it is performing optimally.
- (preventive, medium) Review and optimize the retry logic for the catalog-db calls in the service catalog.

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.42% to 5.47% (+1217%), with a change point at 2026-03-21T15:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.06).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1704 per 5 min before, 1901 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (120 ms before, 216 ms after, +80%).
- **E5** (record, alerts) Upstream catalog-db returning HTTP 503 for catalog (catalog; 2 min after the change; record R017)
- **E6** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 7 min after the change; record R018)
- **E7** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 17 min after the change; record R019)
- **E8** (record, deploys) Deployed catalog v3.27 to eu-west (catalog, eu-west; 224 min before the change; record R014)
- **E9** (record, tickets) catalog-db status page: investigating degraded performance (catalog; 30 min after the change; record R021)
