# INC-013: Why did the p95 latency go up on 16 March 2026?

## What changed
latency_p95_ms for region us-east went from 137.4 to 270.4 (+97%) starting 2026-03-16T04:40:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 126 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Traffic source breakdown (campaigns, bots, partners)

## Possible leads (not confirmed)
1. **The deployment of catalog v3.20 caused the increase in latency and request volume.** (deployment, confidence 30%) [E6, E7]
   - Why: The deployment of catalog v3.20 introduced changes that affected the system's performance.
   - Why: The increase in request volume and error rate coincided with the deployment, indicating a possible correlation.
   - Why: The autoscaler scaling out 4 new instances after the deployment suggests a system response to the increased load.
2. **The error rate increase could be due to the deployment's impact on system stability.** (unknown, confidence 30%) [E4, E6, E7]
   - Why: The error rate increased after the deployment, suggesting a potential issue with the new version.
   - Why: The deployment could have introduced bugs or changes that affected system stability.
   - Why: The autoscaler scaling out new instances indicates the system was under stress.

## Ruled out
- The increase in latency and request volume were due to a configuration change.: No evidence supports a configuration change as the cause. The deployment of a new version is the most supported cause. [E1, E2, E3, E4, E5, E6, E7]
- The increase in latency and request volume were due to a data issue.: No evidence supports a data issue. The increase in request volume and error rate are more aligned with system load and deployment impacts. [E1, E2, E3, E4, E5, E6, E7]
- The increase in latency and request volume were due to a dependency issue with an external service.: No evidence supports a dependency issue. The deployment and increased load are more likely causes. [E1, E2, E3, E4, E5, E6, E7]

## Actions
- (corrective, high) Roll back the catalog v3.20 deployment to revert the changes and observe the system's behavior.
- (preventive, medium) Implement a load balancer to distribute the increased request volume more evenly across servers.
- (preventive, medium) Monitor the system closely for any further issues and adjust the autoscaler as needed.

## Fact-check
- Evidence IDs cited by the model: 29, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region us-east rose from 137 ms to 270 ms (+97%), with a change point at 2026-03-16T04:40:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region us-east: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region us-east rose (2707 per 5 min before, 10491 per 5 min after, +288%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region us-east rose (0.40% before, 0.78% after, +97%).
- **E5** (record, alerts) Request volume 3x normal in us-east (us-east; 12 min after the change; record R009)
- **E6** (record, deploys) Deployed catalog v3.20 to us-east (routine release) (catalog, us-east; 126 min before the change; record R008)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (us-east; 20 min after the change; record R010)
