# INC-023: Why did the p95 latency go up on 09 March 2026?

## What changed
latency_p95_ms for region ap-south went from 136.9 to 290.2 (+112%) starting 2026-03-09T09:05:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (233 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign caused a sudden increase in request volume and error rate.** (traffic, confidence 90%) [E5, E6]
   - Why: The flash sale campaign went live at the change point, causing a surge in requests.
   - Why: The surge in requests led to increased latency as the system could not handle the load.
   - Why: The increased latency resulted in the observed rise in P95 latency.

## Ruled out
- The change was due to a configuration update.: No evidence supports a configuration change. []
- The increase in latency was due to a data quality issue.: No evidence supports a data quality issue. []
- The increase in latency was due to a dependency issue with an external service.: No evidence supports a dependency issue with an external service. []

## Actions
- (corrective, high) Implement a dynamic scaling strategy to better handle sudden spikes in traffic.
- (preventive, high) Monitor request volume and error rates closely during marketing campaigns to detect and respond to sudden spikes.
- (corrective, medium) Optimize the autoscaler to better handle the load during sudden traffic spikes.

## Fact-check
- Evidence IDs cited by the model: 3, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 290 ms (+112%), with a change point at 2026-03-09T09:05:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1230 per 5 min before, 5151 per 5 min after, +319%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.41% before, 0.80% after, +96%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 09:05 UTC (ap-south; 233 min before the change; record R011)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R012)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R013)
