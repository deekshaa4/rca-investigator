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
1. **The auth feature flag change likely increased latency due to a configuration mismatch.** (config_change, confidence 80%) [E5, E1]
   - Why: The auth feature flag was changed to 50% in eu-west, affecting the system's behavior.
   - Why: This change could have introduced a configuration mismatch, leading to increased latency.
   - Why: The increased latency is observed in the P95 latency metric, which is affected by the auth feature flag.
2. **The flash sale campaign likely caused a spike in request volume, increasing latency.** (traffic, confidence 70%) [E6, E1]
   - Why: The flash sale campaign went live in eu-west at 02:35 UTC, coinciding with the change point.
   - Why: The increase in request volume is observed, indicating a sudden surge in traffic.
   - Why: The increased latency is observed in the P95 latency metric, which is affected by the traffic spike.

## Ruled out
- The deployment of auth v3.26 to us-east was the cause.: The deployment to us-east occurred 200 minutes before the change point, which is too early to be the cause. [E9]
- The error rate increase was due to the deployment to us-east.: The error rate increase occurred after the change point, and the deployment to us-east happened before the change. [E9]
- The data quality issues caused the increase in latency.: There is no evidence that the data quality issues were the cause of the increase in latency. []

## Actions
- (corrective, high) Review and revert the auth feature flag change to 50% in eu-west.
- (preventive, medium) Monitor request volume and latency closely during flash sale campaigns and adjust scaling as needed.
- (preventive, medium) Implement a traffic management system to handle sudden spikes in traffic during campaigns.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region eu-west rose from 137 ms to 246 ms (+80%), with a change point at 2026-03-20T02:35:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region eu-west: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region eu-west rose (2132 per 5 min before, 7230 per 5 min after, +239%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region eu-west rose (0.39% before, 0.80% after, +105%).
- **E5** (record, config_changes) Changed auth feature flag new_ui_flow to 50% in eu-west (auth, eu-west; 2 min before the change; record R011)
- **E6** (record, tickets) Marketing: flash sale campaign goes live in eu-west at 02:35 UTC (eu-west; 242 min before the change; record R008)
- **E7** (record, alerts) Request volume 3x normal in eu-west (eu-west; 12 min after the change; record R012)
- **E8** (record, logs) autoscaler: scaling out, 4 new instances requested (eu-west; 20 min after the change; record R013)
- **E9** (record, deploys) Deployed auth v3.26 to us-east (routine release) (auth, us-east; 200 min before the change; record R010)
