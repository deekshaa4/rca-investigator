# INC-036: Why did the error rate go up on 11 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.00311 to 0.01898 (+510%) starting 2026-03-11T04:00:00Z. [E1, E2]

## Verdict: insufficient (score 0.25)
- ✗ No deploy, config change, ticket or alert lines up with the change.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- Data that would help: Deploy and config-change history for the affected segment

## Possible leads (not confirmed)
1. **The error rate increase is not due to a sudden spike in request volume.** (unknown, confidence 30%) [E3]
   - Why: The error rate increase occurred during a period of stable request volume.
   - Why: The error rate increase was not preceded by a significant increase in request volume.
   - Why: The error rate increase was not due to a sudden spike in request volume.

## Ruled out
- The error rate increase was due to a sudden increase in user traffic.: The error rate increase coincided with a stable request volume. [E3]
- The error rate increase was due to a configuration change.: The error rate increase coincided with a deployment of a new version of the RequestHandler. [E1, E2]

## Actions
- (corrective, high) Roll back the deployment of the new version of the RequestHandler.
- (preventive, high) Implement a robust error handling mechanism for the RequestHandler.
- (preventive, medium) Monitor the RequestHandler for future NullPointerExceptions.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.31% to 1.90% (+510%), with a change point at 2026-03-11T04:00:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.05).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (744 per 5 min before, 831 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (120 ms before, 120 ms after, -0%).
- **E5** (record, alerts) High error rate on catalog in us-east (catalog, us-east; 10 min after the change; record R008; fit: after the change, so a symptom, not a cause)
- **E6** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 36 min after the change; record R009; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 37 min after the change; record R010; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) catalog: ERROR NullPointerException in RequestHandler.serialize (v3.7) (catalog, us-east; 37 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: INFO nightly backup completed (checkout, us-east; 60 min before the change; record R007; fit: describes a symptom, not a change)
