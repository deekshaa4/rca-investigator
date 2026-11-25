# INC-012: Why did the p95 latency go up on 16 March 2026?

## What changed
latency_p95_ms for service auth went from 90.47 to 268.5 (+197%) starting 2026-03-16T14:35:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **A sudden increase in connection pool exhaustion warnings caused the p95 latency spike.** (dependency, confidence 30%) [E6, E7, E8]
   - Why: The connection pool exhaustion warnings indicate a failure in the database connection management.
   - Why: This failure is likely due to the new release or version of the service.
   - Why: The new release or version of the service is the cause of the p95 latency spike.
2. **The increase in request volume did not cause the p95 latency spike.** (unknown, confidence 30%) [E3]
   - Why: The request volume for service auth stayed about the same before and after the change.
   - Why: The error rate for service auth increased, indicating a different issue.
   - Why: The error rate increase is more likely the cause of the p95 latency spike.

## Ruled out
- The increase in p95 latency was due to a configuration change.: The change in p95 latency occurred at the same time as the change point, and the error rate increased, suggesting a configuration change is unlikely. [E1]
- The increase in p95 latency was due to a deployment of a new release or version.: The p95 latency spike occurred at the same time as the change point, and the error rate increased, suggesting a deployment is likely the cause. [E1]
- The increase in p95 latency was due to a traffic spike.: The request volume for service auth stayed about the same before and after the change, and the error rate increased, suggesting a traffic spike is unlikely. [E3]
- The increase in p95 latency was due to an infrastructure issue.: The p95 latency spike occurred at the same time as the change point, and the error rate increased, suggesting an infrastructure issue is unlikely. [E1]
- The increase in p95 latency was due to a data issue.: The p95 latency spike occurred at the same time as the change point, and the error rate increased, suggesting a data issue is unlikely. [E1]

## Actions
- (corrective, high) Review and potentially rollback the recent deployment to service auth.
- (preventive, high) Monitor the database connection pool and ensure it is properly configured and monitored.
- (preventive, medium) Review and optimize the database connection management logic in the service auth.

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for service auth rose from 90 ms to 268 ms (+197%), with a change point at 2026-03-16T14:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1125 per 5 min before, 1299 per 5 min after, +15%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for service auth rose (0.38% before, 0.60% after, +61%).
- **E5** (record, alerts) p95 latency above SLO on auth (auth; 15 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E6** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, ap-south; 5 min after the change; record R013; fit: describes a symptom, not a change)
- **E7** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, eu-west; 19 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) auth: WARN connection pool exhausted, waiting for a free connection (auth, us-east; 27 min after the change; record R016; fit: after the change, so a symptom, not a cause)
