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
1. **New deployment of catalog v3.27 introduced issues with upstream catalog-db.** (deployment, confidence 90%) [E1, E3, E4, E5, E6, E7, E8]
   - Why: Deployed catalog v3.27 to eu-west (record R014).
   - Why: The error rate for service catalog increased (record E1).
   - Why: Upstream catalog-db returned HTTP 503 (record E5).
   - Why: Upstream catalog-db timed out after retries (records E6, E7).
2. **Increased load on catalog-db due to deployment.** (traffic, confidence 80%) [E1, E3, E4, E5, E6, E7]
   - Why: The error rate for service catalog increased (record E1).
   - Why: Request volume for service catalog increased (record E3).
   - Why: Upstream catalog-db timed out after retries (records E6, E7).

## Ruled out
- The increase in error rate was due to a config_change.: No evidence supports a config_change. []
- The increase in error rate was due to a data issue.: No evidence supports a data issue. []
- The increase in error rate was due to a dependency issue with an external service.: The issue is with the upstream catalog-db, not an external service. [E5, E6, E7]
- The increase in error rate was due to infrastructure issues.: No evidence supports infrastructure issues. []
- The increase in error rate was due to a known bug.: No evidence supports a known bug. []
- The increase in error rate was due to a sudden spike in users.: Request volume for service catalog did not increase significantly (record E3). [E3]

## Actions
- (corrective, high) Roll back the catalog v3.27 deployment to eu-west.
- (preventive, high) Monitor catalog-db performance and availability closely.
- (preventive, medium) Optimize the catalog-db to handle the increased load.

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
