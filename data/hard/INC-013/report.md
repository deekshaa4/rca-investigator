# INC-013: Why did the p95 latency go up on 16 March 2026?

## What changed
latency_p95_ms for region us-east went from 137.4 to 270.4 (+97%) starting 2026-03-16T04:40:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 126 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✗ The main factor does not rest on this event.
- Data that would help: Change records from the hour before the change

## Possible leads (not confirmed)
1. **The increase in request volume led to higher latency as the system struggled to handle the load.** (traffic, confidence 30%) [E2, E3, E4]
   - Why: The rise in request volume caused the system to become overwhelmed.
   - Why: The increased load required more instances to be scaled out.
   - Why: The autoscaler's response to the load increase resulted in a temporary spike in latency.
   - Why: evidence_ids
2. **The deployment of catalog v3.20 likely introduced a new latency issue.** (deployment, confidence 30%) [E6]
   - Why: The deployment of catalog v3.20 occurred shortly before the change point.
   - Why: The deployment may have introduced a new latency bug or configuration issue.
   - Why: The new version of the catalog could have caused the system to behave differently, leading to higher latency.

## Ruled out
- The deployment of catalog v3.20 was the cause of the increase in latency.: The deployment occurred hours before the change point, making it unlikely to be the cause. [E6]
- The autoscaler's response to the load increase was the cause of the latency spike.: The autoscaler's response occurred after the change point, making it unlikely to be the cause. [E7]

## Actions
- (corrective, high) Roll back the catalog v3.20 deployment to revert any changes that may have introduced the latency issue.
- (preventive, medium) Implement a more granular autoscaler to better handle the load and reduce latency spikes.
- (preventive, medium) Monitor request volume and latency closely and take corrective action if the issue recurs.

## Fact-check
- Evidence IDs cited by the model: 6, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region us-east rose from 137 ms to 270 ms (+97%), with a change point at 2026-03-16T04:40:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region us-east: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region us-east rose (2707 per 5 min before, 10491 per 5 min after, +288%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region us-east rose (0.40% before, 0.78% after, +97%).
- **E5** (record, alerts) Request volume 3x normal in us-east (us-east; 12 min after the change; record R009; fit: after the change, so a symptom, not a cause)
- **E6** (record, deploys) Deployed catalog v3.20 to us-east (routine release) (catalog, us-east; 126 min before the change; record R008; fit: hours before the change, too early to explain a sudden jump)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (us-east; 20 min after the change; record R010; fit: after the change, so a symptom, not a cause)
