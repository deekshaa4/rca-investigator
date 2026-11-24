# INC-037: Why did the p95 latency go up on 06 March 2026?

## What changed
latency_p95_ms for service search went from 140.7 to 361.7 (+157%) starting 2026-03-06T07:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
No contributing factor is supported by the evidence.

## Ruled out
- The increase in latency was due to a new release or version.: No evidence supports a new release or version change. [E1]
- The increase in latency was due to a configuration change.: No evidence supports a configuration change. [E1]
- The increase in latency was due to a change in traffic.: Request volume and error rate did not change significantly. [E3, E4]
- The increase in latency was due to a dependency issue.: No evidence supports a dependency issue. [E1]
- The increase in latency was due to a data issue.: No evidence supports a data issue. [E1]
- The increase in latency was due to an unknown issue.: No evidence supports an unknown issue. [E1]

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service search rose from 141 ms to 362 ms (+157%), with a change point at 2026-03-06T07:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service search: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service search stayed about the same (2428 per 5 min before, 2952 per 5 min after, +22%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service search rose (0.41% before, 0.63% after, +56%).
- **E5** (record, alerts) p95 latency above SLO on search (search; 15 min after the change; record R015)
- **E6** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, eu-west; 9 min after the change; record R014)
- **E7** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, ap-south; 16 min after the change; record R016)
- **E8** (record, logs) search: WARN connection pool exhausted, waiting for a free connection (search, us-east; 20 min after the change; record R017)
- **E9** (record, logs) search: INFO cache warmed in 1.8s (search, us-east; 292 min before the change; record R012)
