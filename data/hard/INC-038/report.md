# INC-038: Why did the p95 latency go up on 26 March 2026?

## What changed
latency_p95_ms for region ap-south went from 137.4 to 298 (+117%) starting 2026-03-26T06:10:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 220 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Traffic source breakdown (campaigns, bots, partners)

## Possible leads (not confirmed)
1. **The deployment of auth v2.23 to ap-south likely caused the increase in p95 latency.** (deployment, confidence 30%) [E6, E1]
   - Why: The deployment of auth v2.23 to ap-south occurred 220 minutes before the change point.
   - Why: The p95 latency increased from 137 ms to 298 ms, a significant increase.
   - Why: The deployment of auth v2.23 is a known change that could affect latency.
   - Why: evidence_ids
2. **The increase in request volume may have contributed to the latency increase.** (traffic, confidence 30%) [E3, E2]
   - Why: The request volume increased from 1236 per 5 min to 5418 per 5 min, a significant increase.
   - Why: The increase in request volume could have overwhelmed the system, leading to higher latency.
   - Why: The deployment of auth v2.23 to ap-south is a known change that could affect request volume.
   - Why: evidence_ids
3. **The increase in error rate may be related to the deployment of auth v2.23.** (unknown, confidence 30%) [E4, E6]
   - Why: The error rate increased from 0.41% to 0.81%, a significant increase.
   - Why: The deployment of auth v2.23 to ap-south is a known change that could affect error rates.
   - Why: The increase in error rate could be a symptom of the deployment of auth v2.23.
   - Why: evidence_ids

## Ruled out
- The increase in latency is due to a configuration change.: No evidence supports a config_change as the cause of the latency increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in latency is due to a dependency issue with an external service.: No evidence supports a dependency issue as the cause of the latency increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]
- The increase in latency is due to an infrastructure issue.: No evidence supports an infrastructure issue as the cause of the latency increase. [E1, E2, E3, E4, E5, E6, E7, E8, E9]

## Actions
- (corrective, high) Roll back the deployment of auth v2.23 to ap-south
- (preventive, medium) Monitor request volume and error rates closely in ap-south
- (preventive, medium) Review and optimize the autoscaler in ap-south

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 298 ms (+117%), with a change point at 2026-03-26T06:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1236 per 5 min before, 5418 per 5 min after, +338%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.41% before, 0.81% after, +97%).
- **E5** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R012)
- **E6** (record, deploys) Deployed auth v2.23 to ap-south (routine release) (auth, ap-south; 220 min before the change; record R009)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R013)
- **E8** (record, deploys) Deployed checkout v2.3 to eu-west (routine release) (checkout, eu-west; 74 min before the change; record R010)
- **E9** (record, logs) auth: WARN slow query 1.2s on report endpoint (single occurrence) (auth, us-east; 63 min before the change; record R011)
