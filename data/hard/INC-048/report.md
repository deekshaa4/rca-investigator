# INC-048: Why did the p95 latency go up on 25 March 2026?

## What changed
latency_p95_ms for region eu-west went from 136.7 to 219.3 (+60%) starting 2026-03-25T08:10:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (162 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign likely increased the load on the system.** (traffic, confidence 90%) [E5, E2, E3, E4]
   - Why: The marketing campaign went live at the right time and place (162 minutes before the change).
   - Why: The increase in request volume and error rate are consistent with a sudden surge in traffic.
   - Why: The rise in p95 latency is also consistent with increased load on the system.
   - Why: evidence_ids

## Ruled out
- The deployment caused the increase in latency.: The change point is at the right time and place, and the increase in latency is a symptom, not a cause. [E1]
- The config change caused the increase in latency.: The change point is at the right time and place, and the increase in latency is a symptom, not a cause. [E1]
- The dependency issue caused the increase in latency.: The increase in latency is a symptom, not a cause. [E1]
- The data quality issue caused the increase in latency.: The increase in latency is a symptom, not a cause. [E1]

## Actions
- (preventive, high) Review and optimize the autoscaler configuration to ensure it scales in a timely manner.
- (preventive, high) Monitor the marketing campaigns and adjust the autoscaler accordingly to avoid similar issues in the future.
- (preventive, medium) Review and possibly reduce the flash sale campaign duration to avoid similar spikes in traffic.

## Fact-check
- Evidence IDs cited by the model: 12, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 219 ms (+60%), with a change point at 2026-03-25T08:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2048 per 5 min before, 9799 per 5 min after, +379%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.37% before, 0.74% after, +102%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 08:10 UTC (eu-west; 162 min before the change; record R011; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R013; fit: after the change, so a symptom, not a cause)
