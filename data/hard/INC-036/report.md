# INC-036: Why did the error rate go up on 11 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.00311 to 0.01898 (+510%) starting 2026-03-11T04:00:00Z. [E1, E2]

## Verdict: insufficient (score 0.15)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✗ A traffic cause is claimed, but request volume did not rise.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **Increased error rate due to higher request volume.** (traffic, confidence 30%) [E2, E3]
   - Why: The error rate increase coincided with a 12% increase in request volume.
   - Why: The error rate spike is not explained by the unchanged request volume.
   - Why: The increase in request volume could have overwhelmed the system, leading to more errors.

## Ruled out
- The error rate increase was due to a configuration change.: No evidence supports a configuration change. The error rate and request volume remained stable. [E1, E2, E3]
- The error rate increase was due to a dependency issue with an external service.: No evidence supports a dependency issue. The error rate and request volume remained stable. [E1, E2, E3]
- The error rate increase was due to a data issue.: No evidence supports a data issue. The error rate and request volume remained stable. [E1, E2, E3]
- The error rate increase was due to infrastructure issues.: No evidence supports infrastructure issues. The error rate and request volume remained stable. [E1, E2, E3]

## Actions
- (corrective, high) Roll back the deployment of the new version of RequestHandler (v3.7).
- (preventive, medium) Monitor request volume and adjust capacity if necessary.
- (preventive, medium) Implement error handling and logging improvements in RequestHandler.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.31% to 1.90% (+510%), with a change point at 2026-03-11T04:00:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.05).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (744 per 5 min before, 831 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (120 ms before, 120 ms after, -0%).
- **E5** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R008)
- **E6** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 36 min after the change; record R009)
- **E7** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 37 min after the change; record R010)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 37 min after the change; record R011)
- **E9** (record, logs) checkout: INFO nightly backup completed (checkout, us-east; 60 min before the change; record R007)
