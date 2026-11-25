# INC-020: Why did the error rate go up on 21 March 2026?

## What changed
error_rate for service search, region ap-south went from 0.004825 to 0.01069 (+122%) starting 2026-03-21T11:55:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 217 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The deployment of search v7.6 to ap-south may have introduced a new issue.** (deployment, confidence 30%) [E5, E1]
   - Why: The deployment of search v7.6 to ap-south caused a change in the error rate.
   - Why: The error rate increased from 0.48% to 1.07% in service search in region ap-south.
   - Why: The deployment of a new version (v7.6) to a new region (ap-south) is a plausible cause of the error rate increase.
2. **The increase in request volume could have contributed to the error rate increase.** (traffic, confidence 30%) [E3, E1]
   - Why: The request volume increased by 23% in service search in region ap-south.
   - Why: The error rate increased from 0.48% to 1.07% in service search in region ap-south.
   - Why: The increase in request volume could have overwhelmed the system, leading to more errors.

## Ruled out
- The increase in error rate is due to a configuration change.: The error rate increased after the deployment, not before or at the same time as the configuration change. [E5, E1]
- The increase in error rate is due to a dependency issue with an upstream service.: There is no evidence of a dependency issue, as the error rate increased in the service itself and not in the upstream service. [E5, E1]
- The increase in error rate is due to a sudden increase in data quality.: There is no evidence of bad or unusual input data, as the error rate increased in the service itself and not in the input data. [E5, E1]
- The increase in error rate is due to a sudden increase in infrastructure capacity.: There is no evidence of a sudden increase in infrastructure capacity, as the error rate increased in the service itself and not in the infrastructure. [E5, E1]

## Actions
- (corrective, high) Roll back the deployment of search v7.6 to ap-south to see if the error rate decreases.
- (preventive, medium) Monitor the system for any further errors and request volume spikes, and take appropriate action if they occur.
- (preventive, medium) Review the logs and metrics for any other services in the region that may have been affected by the deployment.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service search in region ap-south rose from 0.48% to 1.07% (+122%), with a change point at 2026-03-21T11:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service search in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.18).
- **E3** (metric, metrics:requests) At the same time, request volume for service search in region ap-south stayed about the same (511 per 5 min before, 627 per 5 min after, +23%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service search in region ap-south stayed about the same (140 ms before, 138 ms after, -2%).
- **E5** (record, deploys) Deployed search v7.6 to ap-south (search, ap-south; 217 min before the change; record R009; fit: hours before the change, too early to explain a sudden jump)
- **E6** (record, logs) search: WARN slow query 1.2s on report endpoint (single occurrence) (search, us-east; 94 min before the change; record R010; fit: describes a symptom, not a change)
