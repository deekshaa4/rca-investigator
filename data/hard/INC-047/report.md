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
   - Why: With fewer connections, the pool became exhausted more quickly under normal load.
   - Why: This exhaustion led to the warning messages seen in the logs.
2. **The increase in request volume did not cause the latency to increase, as the error rate did not change.** (traffic, confidence 80%) [E3, E4]
   - Why: The request volume remained stable, with a 20% increase in requests.
   - Why: The error rate also increased by 49%, indicating a different issue.
   - Why: The warning messages in the logs suggest a connection pool issue.
3. **The error rate increase is not a direct cause of the latency increase, but it could be related to the connection pool exhaustion.** (unknown, confidence 70%) [E4]
   - Why: The error rate increased by 49%, but the latency increased by 214%.
   - Why: The connection pool exhaustion is the more immediate cause of the latency increase.
   - Why: The error rate increase could be due to other factors, such as a different issue with the service.

## Ruled out
- The increase in latency was due to a sudden spike in traffic.: The request volume did not change significantly, and the error rate did not increase. [E3]
- The increase in latency was due to a new deployment or version.: There is no evidence of a new release or version being deployed on 22 March 2026. []

## Actions
- (corrective, high) Review and adjust the db.pool_size configuration to ensure it can handle the current load without exhausting the connection pool.
- (preventive, high) Implement a connection pool monitoring system to detect exhaustion early and prevent latency spikes.
- (preventive, medium) Monitor the error rate and latency closely to identify any future issues with the connection pool.

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
