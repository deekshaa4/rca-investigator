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
1. **The deployment of auth v2.23 to ap-south likely caused the increase in p95 latency.** (deployment, confidence 30%) [E6, E2]
   - Why: auth v2.23 was deployed to ap-south 220 minutes before the change in p95 latency.
   - Why: The deployment of a new version of the auth service can introduce changes that affect performance.
   - Why: The increase in p95 latency is a symptom of the deployment, not the cause, but it is the most likely explanation given the timing.
2. **The increase in request volume in ap-south contributed to the p95 latency increase.** (traffic, confidence 30%) [E2, E3]
   - Why: The request volume in ap-south increased by 338% after the change.
   - Why: Increased request volume can cause a system to become less responsive, leading to higher p95 latency.
   - Why: The deployment of auth v2.23 to ap-south is the most likely cause of the increased request volume.
3. **The increase in error rate is a symptom of the system under stress, likely caused by the deployment.** (unknown, confidence 30%) [E4, E3]
   - Why: The error rate increased by 97% after the change.
   - Why: Increased error rate is a symptom of the system under stress, which is likely caused by the deployment.
   - Why: The deployment of auth v2.23 to ap-south is the most likely cause of the error rate increase.

## Ruled out
- The deployment of checkout v2.3 to eu-west caused the change in ap-south.: checkout v2.3 was deployed to eu-west 74 minutes before the change in ap-south. [E8]
- The autoscaler scaling out caused the increase in p95 latency.: The autoscaler scaled out 20 minutes after the change in p95 latency. [E7]
- The slow query on the auth service caused the increase in p95 latency.: The slow query occurred 63 minutes before the change in p95 latency. [E9]

## Actions
- (corrective, high) Roll back the auth v2.23 deployment to ap-south
- (preventive, medium) Monitor request volume and error rates in ap-south closely
- (preventive, medium) Review and optimize the performance of the auth service

## Fact-check
- Evidence IDs cited by the model: 9, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 298 ms (+117%), with a change point at 2026-03-26T06:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1236 per 5 min before, 5418 per 5 min after, +338%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.41% before, 0.81% after, +97%).
- **E5** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E6** (record, deploys) Deployed auth v2.23 to ap-south (routine release) (auth, ap-south; 220 min before the change; record R009; fit: hours before the change, too early to explain a sudden jump)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E8** (record, deploys) Deployed checkout v2.3 to eu-west (routine release) (checkout, eu-west; 74 min before the change; record R010; fit: different service/region, so unlikely to be the cause)
- **E9** (record, logs) auth: WARN slow query 1.2s on report endpoint (single occurrence) (auth, us-east; 63 min before the change; record R011; fit: describes a symptom, not a change)
