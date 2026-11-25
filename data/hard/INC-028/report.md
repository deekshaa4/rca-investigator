# INC-028: Why did the p95 latency go up on 12 March 2026?

## What changed
latency_p95_ms for region ap-south went from 137 to 252.1 (+84%) starting 2026-03-12T06:35:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (288 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign likely caused the spike in request volume and error rate.** (traffic, confidence 90%) [E5, E2, E4]
   - Why: The flash sale campaign went live at the change point (E5).
   - Why: This led to a sudden increase in request volume (E2, E4).
   - Why: The increased load caused the system to struggle, leading to higher error rates (E4).
   - Why: evidence_ids

## Ruled out
- The deployment of catalog v6.12 caused the change.: The deployment was in us-east, not ap-south (E8). [E8]
- The routine release of checkout v1.8 caused the change.: The release was 272 minutes before the change (E9). [E9]

## Actions
- (corrective, high) Implement a load balancer to handle sudden spikes in traffic.
- (preventive, high) Optimize the autoscaler to better handle sudden load increases.
- (preventive, medium) Monitor and adjust the autoscaler response time to avoid over-scaling.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 252 ms (+84%), with a change point at 2026-03-12T06:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1235 per 5 min before, 4430 per 5 min after, +259%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.38% before, 0.76% after, +101%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 06:35 UTC (ap-south; 288 min before the change; record R010)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R014)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R015)
- **E8** (record, deploys) Deployed catalog v6.12 to us-east (catalog, us-east; 3 min before the change; record R013)
- **E9** (record, deploys) Deployed checkout v1.8 to us-east (routine release) (checkout, us-east; 272 min before the change; record R011)
