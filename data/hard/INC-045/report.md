# INC-045: Why did the error rate go up on 13 March 2026?

## What changed
error_rate for service search, region eu-west went from 0.004807 to 0.009203 (+91%) starting 2026-03-13T15:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 226 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **A new deployment caused the error rate to spike.** (deployment, confidence 30%) [E5, E1]
   - Why: Search v5.23 deployment increased error rate.
   - Why: Increased error rate led to higher error rate for service search in region eu-west.
   - Why: The deployment occurred hours before the change, indicating it was the cause.
2. **The deployment was not the only change, but it was the most recent.** (unknown, confidence 30%) [E5, E6]
   - Why: Search v5.23 deployment was the most recent change.
   - Why: Other changes (like R010) were routine and did not affect the error rate.
   - Why: The error rate increase was not caused by other changes.

## Ruled out
- The error rate increase was due to a new feature or change in the search v5.23 deployment.: The error rate increase was not accompanied by new features or changes in the search v5.23 deployment. [E5]
- The error rate increase was due to a change in the catalog service.: The catalog service backup did not cause the error rate increase. [E7]

## Actions
- (corrective, high) Roll back the search v5.23 deployment to prevent further error rate increase.
- (preventive, medium) Monitor the search service for any new changes or issues.
- (preventive, medium) Review and test the search v5.23 deployment thoroughly before releasing it.

## Fact-check
- Evidence IDs cited by the model: 6, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region eu-west rose from 0.48% to 0.92% (+91%), with a change point at 2026-03-13T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.23).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region eu-west stayed about the same (880 per 5 min before, 989 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region eu-west stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed search v5.23 to eu-west (search, eu-west; 226 min before the change; record R009; fit: hours before the change, too early to explain a sudden jump)
- **E6** (record, deploys) Deployed search v2.15 to us-east (routine release) (search, us-east; 94 min before the change; record R010; fit: different service/region, so unlikely to be the cause)
- **E7** (record, logs) catalog: INFO nightly backup completed (catalog, us-east; 336 min before the change; record R008; fit: describes a symptom, not a change)
