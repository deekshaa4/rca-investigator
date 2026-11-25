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
1. **New deployment of checkout v2.26 caused increased latency and connection pool exhaustion.** (deployment, confidence 90%) [E5, E1]
   - Why: Checkout v2.26 deployment led to a change in service checkout's performance.
   - Why: The change in checkout v2.26 deployment caused the p95 latency to rise.
   - Why: The increased latency and connection pool exhaustion are symptoms of the deployment change.
2. **Config change to reduce db.pool_size from 50 to 5 led to increased latency and connection pool exhaustion.** (config_change, confidence 80%) [E6, E1]
   - Why: Reducing db.pool_size from 50 to 5 caused a change in service checkout's performance.
   - Why: The reduced db.pool_size deployment change caused the p95 latency to rise.
   - Why: The increased latency and connection pool exhaustion are symptoms of the config change.

## Ruled out
- Increased request volume caused the p95 latency to rise.: Request volume remained about the same before and after the change. [E3]
- Error rate increase was due to external factors.: Error rate increase is a symptom, not a cause. [E4]
- Connection pool exhaustion was due to external factors.: Connection pool exhaustion is a symptom, not a cause. [E7, E8, E9]

## Actions
- (corrective, high) Rollback the deployment of checkout v2.26
- (corrective, high) Rollback the config change to reduce db.pool_size
- (preventive, medium) Monitor and optimize the connection pool size for checkout

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 220 ms to 601 ms (+173%), with a change point at 2026-03-19T15:15:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (852 per 5 min before, 958 per 5 min after, +12%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.43% before, 0.67% after, +55%).
- **E5** (record, deploys) Deployed checkout v2.26 to us-east (checkout, us-east; 2 min before the change; record R017; fit: right time and place: a strong candidate cause)
- **E6** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R018; fit: right time and place: a strong candidate cause)
- **E7** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R020; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 10 min after the change; record R019; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 27 min after the change; record R021; fit: after the change, so a symptom, not a cause)
