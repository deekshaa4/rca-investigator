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
1. **Upstream service catalog-db is experiencing degraded performance, causing errors in the catalog service.** (dependency, confidence 90%) [E5, E6, E7]
   - Why: The catalog service is dependent on the catalog-db service.
   - Why: The catalog-db service is experiencing degraded performance, leading to HTTP 503 errors.
   - Why: These errors are propagated to the catalog service, causing an increase in error rate.

## Ruled out
- The increase in error rate is due to a sudden increase in user traffic.: The request volume for the service catalog did not change significantly. [E3]
- The increase in error rate is due to configuration changes in the catalog service.: There is no evidence of configuration changes that would explain the sudden jump in error rate. [E1, E2, E3, E4]
- The catalog service deployment introduced a new version that may have introduced bugs or performance issues.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E8]

## Actions
- (corrective, high) Investigate and fix the issue with the upstream catalog-db service.

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.42% to 5.47% (+1217%), with a change point at 2026-03-21T15:30:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.06).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1704 per 5 min before, 1901 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (120 ms before, 216 ms after, +80%).
- **E5** (record, alerts) Upstream catalog-db returning HTTP 503 for catalog (catalog; 2 min after the change; record R017; fit: right time and place: a strong candidate cause)
- **E6** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 7 min after the change; record R018; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 17 min after the change; record R019; fit: after the change, so a symptom, not a cause)
- **E8** (record, deploys) Deployed catalog v3.27 to eu-west (catalog, eu-west; 224 min before the change; record R014; fit: hours before the change, too early to explain a sudden jump)
- **E9** (record, tickets) catalog-db status page: investigating degraded performance (catalog; 30 min after the change; record R021; fit: after the change, so a symptom, not a cause)
