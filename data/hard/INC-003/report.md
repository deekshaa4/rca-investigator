# INC-003: Why did the p95 latency go up on 21 March 2026?

## What changed
latency_p95_ms for region ap-south went from 136.6 to 242.7 (+78%) starting 2026-03-21T10:25:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (191 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign went live, causing a sudden increase in request volume and error rate.** (traffic, confidence 90%) [E5, E6, E4]
   - Why: The flash sale campaign triggered a spike in user activity in ap-south.
   - Why: This spike led to a higher request volume and error rate.
   - Why: The increased load caused the p95 latency to rise.

## Ruled out
- The deployment of search v1.26 caused the change.: The deployment was in eu-west, not ap-south. [E9]
- The typo on the help page caused the change.: The help page typo occurred 244 minutes before the change. [E8]

## Actions
- (corrective, high) Implement a more aggressive autoscaler to handle sudden spikes in traffic.
- (preventive, high) Monitor request volume and error rate closely during marketing campaigns to identify and address sudden spikes in traffic.
- (preventive, medium) Optimize the autoscaler configuration to better handle sudden traffic spikes.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 137 ms to 243 ms (+78%), with a change point at 2026-03-21T10:25:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1233 per 5 min before, 4638 per 5 min after, +276%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.35% before, 0.75% after, +114%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 10:25 UTC (ap-south; 191 min before the change; record R014)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R017)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R018)
- **E8** (record, tickets) Customer reports a typo on the help page. (auth, ap-south; 244 min before the change; record R012)
- **E9** (record, deploys) Deployed search v1.26 to eu-west (search, eu-west; 4 min before the change; record R016)
