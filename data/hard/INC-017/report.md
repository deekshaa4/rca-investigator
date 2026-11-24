# INC-017: Why did the p95 latency go up on 19 March 2026?

## What changed
latency_p95_ms for service checkout went from 220.1 to 601.4 (+173%) starting 2026-03-19T15:15:00Z. [E1, E2]

## Verdict: partial (score 0.90)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The deployment of a new version of the checkout service (v2.26) likely caused the increase in p95 latency.** (deployment, confidence 90%) [E5, E1]
   - Why: The deployment of checkout v2.26 occurred 2 minutes before the change point.
   - Why: The change in p95 latency was concentrated in the checkout service.
   - Why: The deployment of a new version of the service is a known cause of performance changes.
2. **The change in the checkout database pool size (from 50 to 5) may have contributed to the increased latency.** (config_change, confidence 80%) [E6, E1]
   - Why: The change in db.pool_size occurred 1 minute before the change point.
   - Why: The change in p95 latency was concentrated in the checkout service.
   - Why: Changes in database configurations can affect performance.

## Ruled out
- The increase in request volume caused the p95 latency to rise.: The request volume for checkout did not change significantly (12% increase). [E3]
- The alerts and logs were unrelated to the change in p95 latency.: The alerts and logs were recorded after the change point and do not explain the increase in p95 latency. [E7, E8, E9]

## Actions
- (corrective, high) Rollback the deployment of checkout v2.26 to us-east.
- (preventive, medium) Increase the db.pool_size back to 50 for all regions.
- (preventive, medium) Monitor the connection pool and adjust as needed to prevent exhaustion.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 220 ms to 601 ms (+173%), with a change point at 2026-03-19T15:15:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (852 per 5 min before, 958 per 5 min after, +12%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.43% before, 0.67% after, +55%).
- **E5** (record, deploys) Deployed checkout v2.26 to us-east (checkout, us-east; 2 min before the change; record R017)
- **E6** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R018)
- **E7** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R020)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 10 min after the change; record R019)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 27 min after the change; record R021)
