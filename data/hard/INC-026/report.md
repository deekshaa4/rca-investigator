# INC-026: Why did the error rate go up on 04 March 2026?

## What changed
error_rate for service auth, region us-east went from 0.003785 to 0.03709 (+880%) starting 2026-03-04T04:55:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (8 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 3 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of auth v2.14 caused the error rate to spike.** (deployment, confidence 90%) [E5, E7, E8]
   - Why: auth v2.14 deployment introduced a new version of the RequestHandler.
   - Why: NullPointerException in RequestHandler.serialize (v2.14) led to errors.
   - Why: Increased error rate observed in service auth in region us-east.

## Ruled out
- Increased error rate due to a sudden surge in traffic.: Request volume and latency stayed about the same. [E3]
- Error rate spike caused by a different deployment.: Deployed search v8.0 to eu-west 9 minutes before the change. [E9]
- No significant changes in request volume or latency.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E2, E3, E4]

## Actions
- (corrective, high) Roll back the auth v2.14 deployment to mitigate the error rate spike.
- (preventive, high) Review and test the RequestHandler in v2.14 to identify and fix the NullPointerException.
- (preventive, medium) Monitor the error rate closely and implement a fallback mechanism for the RequestHandler in v2.14.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region us-east rose from 0.38% to 3.71% (+880%), with a change point at 2026-03-04T04:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region us-east stayed about the same (490 per 5 min before, 564 per 5 min after, +15%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region us-east stayed about the same (90 ms before, 90 ms after, -0%).
- **E5** (record, deploys) Deployed auth v2.14 to us-east (auth, us-east; 8 min before the change; record R010; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on auth in us-east (auth, us-east; 5 min after the change; record R012; fit: describes a symptom, not a change)
- **E7** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.14) (auth, us-east; 3 min after the change; record R011; fit: describes a symptom, not a change)
- **E8** (record, logs) auth: ERROR NullPointerException in RequestHandler.serialize (v2.14) (auth, us-east; 22 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, deploys) Deployed search v8.0 to eu-west (search, eu-west; 9 min before the change; record R009; fit: different service/region, so unlikely to be the cause)
