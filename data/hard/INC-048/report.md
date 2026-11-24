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
1. **The increase in request volume and error rate are likely due to the flash sale campaign going live.** (traffic, confidence 90%) [E5, E6, E7]
   - Why: The flash sale campaign went live at the same time as the change point.
   - Why: Increased request volume led to higher p95 latency.
   - Why: Error rate increased due to the higher load on the system.

## Ruled out
- The increase in latency was due to a configuration change.: No evidence supports a configuration change as the cause. [E1, E2, E3, E4]
- The increase in latency was due to a dependency issue with an external service.: No evidence supports a dependency issue with an external service. [E1, E2, E3, E4]
- The increase in latency was due to a data quality issue.: No evidence supports a data quality issue. [E1, E2, E3, E4]

## Actions
- (preventive, high) Implement a traffic management system to handle sudden spikes in traffic during campaigns.
- (corrective, high) Review and optimize the autoscaler configuration to avoid unnecessary scaling out.
- (preventive, medium) Monitor and adjust the autoscaler to avoid scaling out during sudden traffic spikes.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 219 ms (+60%), with a change point at 2026-03-25T08:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.02).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2048 per 5 min before, 9799 per 5 min after, +379%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.37% before, 0.74% after, +102%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 08:10 UTC (eu-west; 162 min before the change; record R011)
- **E6** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R012)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R013)
