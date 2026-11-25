# INC-040: Why did the error rate go up on 05 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.003775 to 0.007476 (+98%) starting 2026-03-05T06:05:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✓ A change event (deploys) lines up in time (7 min before the change).
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The error rate increase is likely due to a configuration change in the service catalog.** (config_change, confidence 30%) [E2, E3, E5, E6]
   - Why: The error rate increased after a routine release of the search service (record R006).
   - Why: The search service release was not the cause of the error rate increase, as the error rate for the service catalog in us-east did not change.
   - Why: The error rate increase is more likely due to a configuration change in the service catalog, as the request volume and latency did not change significantly.
2. **The error rate increase could be due to a configuration change in the service catalog.** (config_change, confidence 30%) [E2, E3, E5, E6]
   - Why: The error rate increased after a routine release of the search service (record R006).
   - Why: The search service release was not the cause of the error rate increase, as the error rate for the service catalog in us-east did not change.
   - Why: The error rate increase is more likely due to a configuration change in the service catalog, as the request volume and latency did not change significantly.
3. **The error rate increase could be due to a configuration change in the service catalog.** (config_change, confidence 30%) [E2, E3, E5, E6]
   - Why: The error rate increased after a routine release of the search service (record R006).
   - Why: The search service release was not the cause of the error rate increase, as the error rate for the service catalog in us-east did not change.
   - Why: The error rate increase is more likely due to a configuration change in the service catalog, as the request volume and latency did not change significantly.

## Ruled out
- The error rate increase is due to a deployment of a new release of the checkout service.: The checkout service release was in a different region (eu-west) and did not affect the error rate in us-east. [E5]
- The error rate increase is due to a deployment of a new release of the search service.: The search service release was routine and did not affect the error rate in us-east. [E6]
- The error rate increase is due to a slow query on the auth service.: The slow query occurred 139 minutes before the error rate increase, and the error rate did not change significantly. [E7]

## Actions
- (corrective, high) Review and update the configuration of the service catalog in us-east.
- (preventive, medium) Implement monitoring for the service catalog in us-east to detect similar issues in the future.
- (preventive, medium) Perform a thorough review of the service catalog's configuration changes in the last few months.

## Fact-check
- Evidence IDs cited by the model: 15, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.38% to 0.75% (+98%), with a change point at 2026-03-05T06:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.10).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (731 per 5 min before, 863 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (120 ms before, 121 ms after, +1%).
- **E5** (record, deploys) Deployed checkout v8.10 to eu-west (checkout, eu-west; 7 min before the change; record R008; fit: different service/region, so unlikely to be the cause)
- **E6** (record, deploys) Deployed search v4.8 to us-east (routine release) (search, us-east; 265 min before the change; record R006; fit: different service/region, so unlikely to be the cause)
- **E7** (record, logs) auth: WARN slow query 1.2s on report endpoint (single occurrence) (auth, ap-south; 139 min before the change; record R007; fit: describes a symptom, not a change)
