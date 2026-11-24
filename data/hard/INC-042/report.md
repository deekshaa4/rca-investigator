# INC-042: Why did the p95 latency go up on 13 March 2026?

## What changed
latency_p95_ms for service checkout went from 221.6 to 698.1 (+215%) starting 2026-03-13T11:50:00Z. [E1, E2]

## Verdict: partial (score 0.90)
- ✓ A change event (deploys) lines up in time (1 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **Deployed checkout v3.17 to ap-south (1 min before the change, found by the engines).** (deployment, confidence 100%) [E5]

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service checkout rose from 222 ms to 698 ms (+215%), with a change point at 2026-03-13T11:50:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service checkout: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout stayed about the same (822 per 5 min before, 1008 per 5 min after, +23%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service checkout rose (0.45% before, 0.65% after, +45%).
- **E5** (record, deploys) Deployed checkout v3.17 to ap-south (checkout, ap-south; 1 min before the change; record R015)
- **E6** (record, config_changes) Changed checkout db.pool_size from 50 to 5 (all regions) (checkout; 1 min before the change; record R014)
- **E7** (record, alerts) p95 latency above SLO on checkout (checkout; 15 min after the change; record R017)
- **E8** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, us-east; 8 min after the change; record R016)
- **E9** (record, logs) checkout: WARN connection pool exhausted, waiting for a free connection (checkout, ap-south; 18 min after the change; record R018)
