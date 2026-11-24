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
1. **The deployment of the search v3.1 to eu-west increased request volume and led to higher p95 latency.** (deployment, confidence 30%) [E7, E8, E9]
   - Why: The deployment of search v3.1 to eu-west caused a surge in request volume.
   - Why: The surge in request volume overwhelmed the autoscaler, leading to scaling out and increased latency.
   - Why: The increased latency resulted in the observed p95 latency rise.
2. **The change in the checkout feature flag led to a flash sale campaign, increasing request volume.** (config_change, confidence 30%) [E5, E6, E7]
   - Why: The change in the checkout feature flag triggered the flash sale campaign.
   - Why: The flash sale campaign increased request volume, which in turn caused the p95 latency rise.
   - Why: The increased request volume overwhelmed the system, leading to higher latency.
3. **The rise in request volume due to the flash sale campaign caused the autoscaler to scale out, leading to higher p95 latency.** (traffic, confidence 30%) [E6, E7, E9]
   - Why: The flash sale campaign increased request volume.
   - Why: The increased request volume caused the autoscaler to scale out.
   - Why: The scaling out led to higher p95 latency.

## Ruled out
- The autoscaler scaling out was due to a bug in the autoscaler itself.: There is no evidence that the autoscaler scaling out was due to a bug. The evidence points to the flash sale campaign as the cause. [E9]
- The increase in p95 latency was due to a configuration issue in the search service.: The deployment of search v3.1 was routine and did not indicate a configuration issue. The evidence points to the flash sale campaign as the cause. [E8]

## Actions
- (corrective, high) Roll back the search v3.1 deployment to eu-west.
- (preventive, medium) Monitor the autoscaler and ensure it is configured correctly to avoid scaling out during normal operations.
- (preventive, medium) Review and optimize the autoscaler configuration to handle sudden spikes in request volume more gracefully.

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
