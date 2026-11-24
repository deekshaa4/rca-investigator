# INC-040: Why did the error rate go up on 05 March 2026?

## What changed
error_rate for service catalog, region us-east went from 0.003775 to 0.007476 (+98%) starting 2026-03-05T06:05:00Z. [E1, E2]

## Verdict: insufficient (score 0.40)
- ✓ A change event (deploys) lines up in time (7 min before the change).
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **The deployment of checkout v8.10 to eu-west may have caused the error rate to increase in us-east.** (deployment, confidence 30%) [E5, E1]
   - Why: checkout v8.10 deployment to eu-west introduced a change that affected service catalog in us-east.
   - Why: The change in checkout v8.10 deployment caused an error rate increase in service catalog in us-east.
   - Why: The error rate increase in service catalog in us-east is reflected in the error rate metric.
   - Why: evidence_ids
2. **The deployment of search v4.8 to us-east may have caused the error rate to increase in us-east.** (deployment, confidence 30%) [E6, E1]
   - Why: search v4.8 deployment to us-east introduced a change that affected service catalog in us-east.
   - Why: The change in search v4.8 deployment caused an error rate increase in service catalog in us-east.
   - Why: The error rate increase in service catalog in us-east is reflected in the error rate metric.
   - Why: evidence_ids
3. **The slow query on the auth endpoint in ap-south may have caused the error rate to increase in us-east.** (unknown, confidence 30%) [E7, E1]
   - Why: The slow query on the auth endpoint in ap-south may have caused a delay in processing requests.
   - Why: This delay may have affected the service catalog in us-east, causing an error rate increase.
   - Why: The error rate increase in service catalog in us-east is reflected in the error rate metric.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a sudden increase in request volume.: The request volume for service catalog in us-east did not change significantly. [E3]
- The increase in error rate was due to a sudden increase in p95 latency.: The p95 latency for service catalog in us-east did not change significantly. [E4]

## Actions
- (corrective, high) Rollback the checkout v8.10 deployment to eu-west.
- (preventive, medium) Monitor the performance of the search v4.8 deployment to us-east closely.
- (preventive, medium) Investigate the slow query on the auth endpoint in ap-south further.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog in region us-east rose from 0.38% to 0.75% (+98%), with a change point at 2026-03-05T06:05:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog in region us-east: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.10).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog in region us-east stayed about the same (731 per 5 min before, 863 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog in region us-east stayed about the same (120 ms before, 121 ms after, +1%).
- **E5** (record, deploys) Deployed checkout v8.10 to eu-west (checkout, eu-west; 7 min before the change; record R008)
- **E6** (record, deploys) Deployed search v4.8 to us-east (routine release) (search, us-east; 265 min before the change; record R006)
- **E7** (record, logs) auth: WARN slow query 1.2s on report endpoint (single occurrence) (auth, ap-south; 139 min before the change; record R007)
