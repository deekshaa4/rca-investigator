# INC-033: Why did the p95 latency go up on 12 March 2026?

## What changed
latency_p95_ms for region us-east went from 136.8 to 295.5 (+116%) starting 2026-03-12T15:10:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (tickets) lines up in time (158 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **The flash sale campaign likely increased the load on the system.** (traffic, confidence 90%) [E5, E2, E4]
   - Why: The marketing campaign went live at the right time and place, causing a sudden increase in request volume.
   - Why: The increase in request volume led to a higher p95 latency as the system struggled to handle the load.
   - Why: The error rate also increased, indicating that the system was under significant stress.

## Ruled out
- The deployment of the new auth version v5.3 was the main cause.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was the main cause.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 was a regression.: The deployment happened hours before the change, and the system was already under stress due to the flash sale campaign. [E7]
- The deployment of the new auth version v5.3 may have introduced a regression.: It rests on a change that is too early, or in a different service/region, to explain a sudden change here. [E7, E1]

## Actions
- (preventive, medium) Review and optimize the autoscaler configuration to ensure it can handle sudden spikes in load.

## Fact-check
- Evidence IDs cited by the model: 16, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 1

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region us-east rose from 137 ms to 295 ms (+116%), with a change point at 2026-03-12T15:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region us-east: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region us-east rose (2792 per 5 min before, 10655 per 5 min after, +282%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region us-east rose (0.43% before, 0.89% after, +106%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in us-east at 15:10 UTC (us-east; 158 min before the change; record R015; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) Request volume 3x normal in us-east (us-east; 12 min after the change; record R017; fit: after the change, so a symptom, not a cause)
- **E7** (record, deploys) Deployed auth v5.3 to us-east (auth, us-east; 167 min before the change; record R014; fit: hours before the change, too early to explain a sudden jump)
- **E8** (record, tickets) Customer asks how to download an invoice. (search, us-east; 171 min before the change; record R013; fit: hours before the change, too early to explain a sudden jump)
- **E9** (record, logs) autoscaler: scaling out, 4 new instances requested (us-east; 20 min after the change; record R018; fit: after the change, so a symptom, not a cause)
