# INC-033: Why did the p95 latency go up on 12 March 2026?

## What changed
latency_p95_ms for region us-east went from 136.8 to 295.5 (+116%) starting 2026-03-12T15:10:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✗ The closest change event is 167 min before the change, too far to be convincing.
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✗ Request volume also rose, so a traffic explanation is still open.
- ✗ 2 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Traffic source breakdown (campaigns, bots, partners); Details to tell the competing changes apart (e.g. a rollback test)

## Possible leads (not confirmed)
1. **The deployment of a new authentication version caused the increase in latency and request volume.** (deployment, confidence 30%) [E7, E2, E4, E9]
   - Why: The deployment of auth v5.3 led to increased request volume and latency.
   - Why: The increased request volume overwhelmed the system, causing autoscaler to scale out.
   - Why: The scaling out process increased latency due to the load balancing and resource allocation delays.
2. **The flash sale campaign likely caused the spike in request volume and error rate.** (traffic, confidence 30%) [E5, E6, E3]
   - Why: The flash sale campaign went live, causing a sudden increase in request volume.
   - Why: The increased request volume overwhelmed the system, leading to higher error rates.
   - Why: The system's inability to handle the sudden surge in traffic caused the observed latency and error rate spikes.

## Ruled out
- The autoscaler scaling out was the cause of the increase in latency.: The autoscaler scaling out happened after the change, not before. [E9]
- The customer support request was the cause of the increase in latency and error rate.: The customer support request happened before the change. [E8]

## Actions
- (corrective, high) Roll back the deployment of auth v5.3 to mitigate the increased latency and request volume.
- (preventive, high) Implement traffic management and load balancing to handle sudden spikes in request volume.
- (preventive, medium) Optimize the system's capacity and performance to better handle the expected traffic during campaigns.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region us-east rose from 137 ms to 295 ms (+116%), with a change point at 2026-03-12T15:10:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region us-east: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region us-east rose (2792 per 5 min before, 10655 per 5 min after, +282%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region us-east rose (0.43% before, 0.89% after, +106%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in us-east at 15:10 UTC (us-east; 158 min before the change; record R015)
- **E6** (record, alerts) Request volume 3x normal in us-east (us-east; 12 min after the change; record R017)
- **E7** (record, deploys) Deployed auth v5.3 to us-east (auth, us-east; 167 min before the change; record R014)
- **E8** (record, tickets) Customer asks how to download an invoice. (search, us-east; 171 min before the change; record R013)
- **E9** (record, logs) autoscaler: scaling out, 4 new instances requested (us-east; 20 min after the change; record R018)
