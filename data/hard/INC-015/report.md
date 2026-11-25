# INC-015: Why did the error rate go up on 15 March 2026?

## What changed
error_rate for service search, region us-east went from 0.004841 to 0.01119 (+131%) starting 2026-03-15T04:10:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✓ A change event (deploys) lines up in time (4 min before the change).
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The error rate increase is likely due to a configuration change in the service search.** (config_change, confidence 30%) [E2, E3, E4, E5, E6]
   - Why: The error rate increased after a routine release of catalog v2.24, which could have introduced a configuration issue.
   - Why: The error rate increase is specific to the service search in region us-east, which is the only service/region that changed.
   - Why: The request volume and latency did not change, suggesting the issue is not related to external factors.
2. **The error rate increase could be due to a configuration change in the service search.** (config_change, confidence 30%) [E2, E3, E4, E5, E6]
   - Why: The error rate increase is specific to the service search in region us-east, which is the only service/region that changed.
   - Why: The request volume and latency did not change, suggesting the issue is not related to external factors.
   - Why: The error rate increase is likely due to a configuration change, as the service search is the only service/region that changed.

## Ruled out
- The error rate increase is due to a deployment of catalog v4.12.: The catalog v4.12 deployment was in a different region (ap-south) and occurred 4 minutes before the error rate increase. [E5]
- The error rate increase is due to a deployment of catalog v2.24.: The catalog v2.24 deployment was in a different region (eu-west) and occurred 166 minutes before the error rate increase. [E6]

## Actions
- (corrective, high) Review and correct the configuration change in the service search in region us-east.
- (preventive, medium) Implement a configuration change monitoring tool to detect and alert on configuration changes in the service search.
- (preventive, medium) Review and optimize the configuration change process to ensure it does not affect other regions.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region us-east rose from 0.48% to 1.12% (+131%), with a change point at 2026-03-15T04:10:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.11).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region us-east stayed about the same (1114 per 5 min before, 1250 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region us-east stayed about the same (141 ms before, 140 ms after, -1%).
- **E5** (record, deploys) Deployed catalog v4.12 to ap-south (catalog, ap-south; 4 min before the change; record R007; fit: different service/region, so unlikely to be the cause)
- **E6** (record, deploys) Deployed catalog v2.24 to eu-west (routine release) (catalog, eu-west; 166 min before the change; record R006; fit: different service/region, so unlikely to be the cause)
