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
1. **The flash sale campaign went live, causing a surge in traffic and errors.** (traffic, confidence 90%) [E5, E4, E3]
   - Why: The flash sale campaign increased the number of requests and errors.
   - Why: The increased traffic overwhelmed the system, leading to higher latency and error rates.
   - Why: The system could not handle the sudden increase in load, resulting in the observed latency and error rates.
2. **The system was already under stress due to the flash sale campaign.** (unknown, confidence 80%) [E5, E6, E7, E8, E9]
   - Why: The system was already under stress due to the flash sale campaign.
   - Why: The system could not scale quickly enough to handle the increased load.
   - Why: The deployment of catalog v6.12 and checkout v1.8 did not address the root cause of the issue.

## Ruled out
- The deployment of catalog v6.12 and checkout v1.8 caused the issue.: The deployments were in different regions and were routine releases, not related to the observed issue. [E8, E9]
- The autoscaler scaling out caused the issue.: The autoscaler scaling out occurred after the change, and the issue was already present. [E7]

## Actions
- (corrective, high) Implement traffic management and load balancing to handle sudden spikes in traffic.
- (preventive, high) Optimize the system's capacity and performance to handle the expected traffic during campaigns.
- (preventive, medium) Monitor and analyze the system's performance during campaigns to identify and address potential issues proactively.

## Fact-check
- Evidence IDs cited by the model: 11, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 252 ms (+84%), with a change point at 2026-03-12T06:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1235 per 5 min before, 4430 per 5 min after, +259%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.38% before, 0.76% after, +101%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 06:35 UTC (ap-south; 288 min before the change; record R010; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E8** (record, deploys) Deployed catalog v6.12 to us-east (catalog, us-east; 3 min before the change; record R013; fit: different service/region, so unlikely to be the cause)
- **E9** (record, deploys) Deployed checkout v1.8 to us-east (routine release) (checkout, us-east; 272 min before the change; record R011; fit: different service/region, so unlikely to be the cause)
