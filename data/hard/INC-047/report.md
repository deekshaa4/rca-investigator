# INC-047: Why did the p95 latency go up on 22 March 2026?

## What changed
latency_p95_ms for service checkout went from 220.9 to 692.8 (+214%) starting 2026-03-22T13:05:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The change in db.pool_size caused the connection pool to be exhausted, leading to increased latency.** (config_change, confidence 90%) [E5, E7, E8, E9]
   - Why: The db.pool_size was changed from 50 to 5, reducing the number of available connections.
   - Why: With fewer connections, the pool could not handle the increased load, causing exhaustion.
   - Why: Exhausted connections led to longer wait times, increasing p95 latency.
2. **The increase in request volume did not explain the p95 latency increase.** (unknown, confidence 80%) [E3]
   - Why: The request volume remained stable, contradicting the idea that more requests caused the issue.

## Ruled out
- The increase in p95 latency was due to a sudden spike in user traffic.: The request volume did not change significantly, contradicting this hypothesis. [E3]
- The increase in p95 latency was caused by a new dependency issue.: There is no evidence of a new external service failure or slowdown. []

## Actions
- (corrective, high) Reduce the db.pool_size back to 50 to prevent future connection pool exhaustion.
- (preventive, medium) Monitor the connection pool closely and adjust db.pool_size as needed.
- (preventive, medium) Review and optimize the checkout service's connection pool management.

## Fact-check
- Evidence IDs cited by the model: 6, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 221 ms to 693 ms (+214%), with a change point at 2026-03-22T13:05:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (833 per 5 min before, 997 per 5 min after, +20%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.33% before, 0.49% after, +49%).
- **E5** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 2 min before the change; record R009)
- **E6** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R011)
- **E7** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, eu-west; 6 min after the change; record R010)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 20 min after the change; record R012)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 21 min after the change; record R013)
