# INC-043: Why did the p95 latency go up on 26 March 2026?

## What changed
latency_p95_ms for region eu-west went from 137 to 224.2 (+64%) starting 2026-03-26T13:45:00Z. [E1, E2]

## Verdict: partial (score 0.80)
- ✓ A change event (config_changes) lines up in time (3 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Traffic source breakdown (campaigns, bots, partners); Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The new UI flow feature flag change led to increased user interaction and higher request volume, causing the p95 latency to rise.** (config_change, confidence 90%) [E5, E2, E7, E8]
   - Why: The new UI flow feature flag was enabled, increasing user interaction.
   - Why: Increased user interaction led to higher request volume.
   - Why: Higher request volume caused the autoscaler to scale out, increasing the number of instances.
   - Why: More instances did not scale the latency down as expected, leading to a rise in p95 latency.
2. **The flash sale campaign went live, causing a sudden increase in user activity.** (traffic, confidence 80%) [E6, E2, E7, E8]
   - Why: The flash sale campaign went live, increasing user activity.
   - Why: Increased user activity led to higher request volume.
   - Why: Higher request volume caused the autoscaler to scale out, increasing the number of instances.
   - Why: More instances did not scale the latency down as expected, leading to a rise in p95 latency.

## Ruled out
- The deployment of search v3.1 caused the increase in p95 latency.: The deployment was routine and occurred hours before the change, not at the right time and place. [E8]
- The autoscaler scaling out was the cause of the p95 latency increase.: The autoscaler scaling out occurred after the change, not at the right time and place. [E7]

## Actions
- (corrective, high) Roll back the new UI flow feature flag change to eu-west.
- (preventive, high) Monitor for similar campaigns and prepare a rollback plan if a similar campaign goes live.
- (preventive, medium) Review and optimize the autoscaler configuration for eu-west.

## Fact-check
- Evidence IDs cited by the model: 10, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 224 ms (+64%), with a change point at 2026-03-26T13:45:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2118 per 5 min before, 7734 per 5 min after, +265%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.48% before, 0.97% after, +102%).
- **E5** (record, config_changes) Changed checkout feature flag new_ui_flow to 50% in eu-west (checkout, eu-west; 3 min before the change; record R016; fit: right time and place: a strong candidate cause)
- **E6** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 13:45 UTC (eu-west; 220 min before the change; record R014; fit: right time and place: a strong candidate cause)
- **E7** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E8** (record, deploys) Deployed search v3.1 to eu-west (routine release) (search, eu-west; 136 min before the change; record R015; fit: hours before the change, too early to explain a sudden jump)
- **E9** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R018; fit: after the change, so a symptom, not a cause)
