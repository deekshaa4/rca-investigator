# INC-003: Why did the p95 latency go up on 21 March 2026?

## What changed
latency_p95_ms for region ap-south went from 136.3 to 241.7 (+77%) starting 2026-03-21T10:25:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (191 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign likely caused a sudden increase in request volume and errors.** (traffic, confidence 90%) [E5, E6, E7]
   - Why: The flash sale campaign went live at 10:25 UTC, 191 minutes before the change.
   - Why: This led to a 276% increase in request volume, overwhelming the system.
   - Why: The error rate also spiked to 0.72%, indicating a system under strain.

## Ruled out
- The typo on the help page caused the change.: The help page issue occurred 178 minutes before the change, well before the increase in request volume and error rate. [E8]
- The customer asking about downloading an invoice caused the change.: The customer support issue occurred 341 minutes before the change, far before the increase in request volume and error rate. [E9]

## Actions
- (corrective, high) Implement a traffic management system to handle sudden spikes in request volume.
- (preventive, medium) Optimize the autoscaler to better handle sudden load increases without causing further issues.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 136 ms to 242 ms (+77%), with a change point at 2026-03-21T10:25:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1234 per 5 min before, 4642 per 5 min after, +276%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.35% before, 0.72% after, +109%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 10:25 UTC (ap-south; 191 min before the change; record R008)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R010)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R011)
- **E8** (record, tickets) Customer reports a typo on the help page. (checkout, us-east; 178 min before the change; record R009)
- **E9** (record, tickets) Customer asks how to download an invoice. (search, us-east; 341 min before the change; record R007)
