# INC-043: Why did the p95 latency go up on 26 March 2026?

## What changed
latency_p95_ms for region eu-west went from 137 to 224.2 (+64%) starting 2026-03-26T13:45:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 136 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✗ 2 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Traffic source breakdown (campaigns, bots, partners); Details to tell the competing changes apart (e.g. a rollback test)

## Possible leads (not confirmed)
1. **The deployment of a new search version caused the increase in latency and request volume.** (deployment, confidence 30%) [E7, E8, E9]
   - Why: The deployment of search v3.1 led to a spike in request volume and increased latency.
   - Why: The increased request volume overwhelmed the autoscaler, which triggered scaling out.
   - Why: The scaling out process took time, causing a delay in response times.
2. **The config change to the checkout feature flag likely contributed to the increase in latency.** (config_change, confidence 30%) [E5, E6, E3]
   - Why: The new_ui_flow feature flag change introduced a new path in the checkout process.
   - Why: This new path may have introduced inefficiencies or bugs that affected latency.
   - Why: The increased request volume due to the flash sale campaign exacerbated the issue.
3. **The flash sale campaign likely caused the spike in request volume and error rate.** (traffic, confidence 30%) [E6, E7, E3]
   - Why: The flash sale campaign led to a sudden increase in user traffic.
   - Why: This increased traffic overwhelmed the system, leading to higher request volume and error rates.
   - Why: The autoscaler scaling out process coincided with the flash sale campaign, further straining the system.

## Ruled out
- The autoscaler scaling out was the main cause.: The autoscaler scaling out happened after the change, not before. [E9]
- The error rate increase was due to a bug in the new search version.: The error rate increase is correlated with the deployment of the new search version, but not caused by it. [E4, E8]
- The config change was the main cause.: The config change happened before the deployment, not after. [E5, E3]

## Actions
- (corrective, high) Roll back the search v3.1 deployment to eu-west.
- (preventive, medium) Monitor the checkout feature flag and rollback if issues arise.
- (preventive, high) Prepare for future flash sale campaigns by increasing capacity and optimizing the checkout process.

## Fact-check
- Evidence IDs cited by the model: 14, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 224 ms (+64%), with a change point at 2026-03-26T13:45:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2118 per 5 min before, 7734 per 5 min after, +265%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.48% before, 0.97% after, +102%).
- **E5** (record, config_changes) Changed checkout feature flag new_ui_flow to 50% in eu-west (checkout, eu-west; 3 min before the change; record R016)
- **E6** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 13:45 UTC (eu-west; 220 min before the change; record R014)
- **E7** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R017)
- **E8** (record, deploys) Deployed search v3.1 to eu-west (routine release) (search, eu-west; 136 min before the change; record R015)
- **E9** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R018)
