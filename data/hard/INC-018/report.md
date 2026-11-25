# INC-018: Why did the p95 latency go up on 20 March 2026?

## What changed
latency_p95_ms for region eu-west went from 136.7 to 245.9 (+80%) starting 2026-03-20T02:35:00Z. [E1, E2]

## Verdict: partial (score 0.80)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Traffic source breakdown (campaigns, bots, partners); Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The new UI flow feature flag change likely caused the increase in latency.** (config_change, confidence 90%) [E5, E1]
   - Why: The new UI flow feature flag change to 50% in eu-west led to increased latency.
   - Why: Increased latency is a known side effect of feature flag changes.
   - Why: The change in feature flag occurred 2 minutes before the latency increase, supporting a temporal relationship.
2. **The flash sale campaign likely caused the increase in request volume and error rate.** (traffic, confidence 80%) [E4, E2, E6]
   - Why: The flash sale campaign went live at the same time as the latency increase.
   - Why: The increase in request volume and error rate are consistent with a sudden spike in traffic.
   - Why: The campaign is a known cause of such spikes in traffic and errors.

## Ruled out
- The deployment of auth v3.26 to us-east was the cause.: The deployment was in a different region and service, making it unlikely to be the cause. [E9]

## Actions
- (corrective, high) Roll back the new UI flow feature flag change to 50% in eu-west.
- (preventive, high) Implement traffic management and rate limiting for the flash sale campaign.
- (preventive, medium) Monitor and adjust the autoscaler to prevent unnecessary scaling out.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 246 ms (+80%), with a change point at 2026-03-20T02:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2132 per 5 min before, 7230 per 5 min after, +239%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.39% before, 0.80% after, +105%).
- **E5** (record, config_changes) Changed auth feature flag new_ui_flow to 50% in eu-west (auth, eu-west; 2 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E6** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 02:35 UTC (eu-west; 242 min before the change; record R008; fit: right time and place: a strong candidate cause)
- **E7** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, deploys) Deployed auth v3.26 to us-east (routine release) (auth, us-east; 200 min before the change; record R010; fit: different service/region, so unlikely to be the cause)
