# INC-032: Why did the p95 latency go up on 05 March 2026?

## What changed
latency_p95_ms for service search went from 140.2 to 290.1 (+107%) starting 2026-03-05T03:15:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The increase in p95 latency is due to a reduction in the search db.pool_size, leading to connection pool exhaustion.** (config_change, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: The config_change (E5) reduced the search db.pool_size from 50 to 5.
   - Why: This reduction in pool size caused the connection pool to become exhausted.
   - Why: The exhausted pool led to the WARN connection pool exhausted, waiting for a free connection (E6, E7, E8, E9).
   - Why: This resulted in increased latency, as the system had to wait for connections to become available.
   - Why: evidence_ids
2. **The increase in p95 latency is also due to the increase in request volume, which put additional strain on the system.** (traffic, confidence 80%) [E3, E5, E6, E7, E8, E9]
   - Why: The request volume for service search increased by 9% (E3).
   - Why: This increase in requests put additional strain on the system.
   - Why: The reduced connection pool size (E5) exacerbated the strain, leading to connection pool exhaustion (E6, E7, E8, E9).
   - Why: The connection pool exhaustion resulted in increased latency (E7, E8, E9).
   - Why: evidence_ids

## Ruled out
- The increase in p95 latency is due to a bug in the search service code.: There is no evidence of a code change or error logs indicating a bug. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in p95 latency is due to a sudden spike in external traffic.: The error rate only increased by 53% (E4), not enough to explain the 107% increase in p95 latency. [E1, E2, E3, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Increase the search db.pool_size back to 50 to prevent connection pool exhaustion.
- (preventive, high) Monitor request volume and adjust capacity if it exceeds current limits.
- (preventive, medium) Review and optimize the search service's connection management to handle higher request volumes.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service search rose from 140 ms to 290 ms (+107%), with a change point at 2026-03-05T03:15:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2514 per 5 min before, 2741 per 5 min after, +9%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service search rose (0.40% before, 0.62% after, +53%).
- **E5** (record, config_changes) Changed search db.pool_size from 50 to 5 (all regions) (search; 2 min before the change; record R011)
- **E6** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, eu-west; 3 min after the change; record R012)
- **E7** (record, alerts) p95 latency above SLO on search (search; 15 min after the change; record R013)
- **E8** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, ap-south; 20 min after the change; record R014)
- **E9** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, us-east; 26 min after the change; record R015)
