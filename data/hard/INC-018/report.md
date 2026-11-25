# INC-018: Why did the p95 latency go up on 20 March 2026?

## What changed
latency_p95_ms for region eu-west went from 136.7 to 245.9 (+80%) starting 2026-03-20T02:35:00Z. [E1, E2]

## Verdict: partial (score 0.90)
- ✓ A change event (tickets) lines up in time (242 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 2 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume rose, as a traffic cause requires.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The increase in request volume and error rate are likely due to the flash sale campaign going live.** (traffic, confidence 90%) [E6, E7, E8]
   - Why: The flash sale campaign went live at 02:35 UTC, causing a surge in request volume.
   - Why: The surge in requests led to increased load on the system, causing higher latency.
   - Why: The increased load also resulted in higher error rates due to system strain.
2. **The change in auth feature flag could have contributed to the increase in latency.** (config_change, confidence 70%) [E5, E1]
   - Why: The auth feature flag was changed to 50% at the same time as the latency spike.
   - Why: The change in feature flag may have affected the system's performance.
   - Why: The system may have been underperforming due to the change, leading to increased latency.
3. **The deployment of auth v3.26 could have caused the latency spike.** (deployment, confidence 60%) [E9, E1]
   - Why: The auth v3.26 deployment happened 200 minutes before the change point.
   - Why: The deployment could have introduced a bug or incompatibility.
   - Why: This could have led to increased latency and error rates.

## Ruled out
- The increase in latency was due to a bug in the autoscaler.: The autoscaler scaling out happened 20 minutes after the change point. [E7, E8]
- The increase in latency was due to a data issue.: There is no evidence of bad or unusual input data. [E1, E2, E3, E4]

## Actions
- (corrective, high) Roll back the auth feature flag change to 50%.
- (preventive, medium) Review the auth v3.26 deployment for any issues.
- (preventive, medium) Monitor request volume and error rates closely in the future.

## Fact-check
- Evidence IDs cited by the model: 13, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

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
