# INC-025: Why did the error rate go up on 09 March 2026?

## What changed
error_rate for service auth, region eu-west went from 0.002781 to 0.006804 (+145%) starting 2026-03-09T15:15:00Z. [E1, E2]

## Verdict: insufficient (score 0.35)
- ✗ The closest change event is 287 min before the change, too far to be convincing.
- ✗ It concerns a different service/region than the one that changed.
- ✗ No logs or alerts from the affected segment confirm the problem.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.
- Data that would help: Change records from the hour before the change; Change records for the affected service/region; Error logs or traces from the affected segment after the change

## Possible leads (not confirmed)
1. **New feature request introduced unexpected load.** (unknown, confidence 30%) [E5]
   - Why: Feature request R013 for dark mode was submitted 287 minutes before the error rate spike.
   - Why: The feature request likely caused a temporary increase in load on the service.
   - Why: This increase in load led to the observed error rate spike.
2. **Service auth in region eu-west experienced a configuration change.** (config_change, confidence 30%) [E1, E2, E3]
   - Why: Service auth in region eu-west saw a change in error rate and request volume.
   - Why: The change in error rate coincided with the introduction of the feature request.
   - Why: The configuration change could have introduced a bug or unexpected behavior.
3. **Service auth in region eu-west saw a spike in p95 latency.** (unknown, confidence 30%) [E4]
   - Why: Service auth in region eu-west had a spike in p95 latency.
   - Why: The spike in latency could be due to the feature request or configuration change.
   - Why: The spike in latency could also indicate a problem with the service itself.

## Ruled out
- The increase in error rate was due to a sudden increase in traffic.: Request volume stayed about the same, contradicting this hypothesis. [E3]
- The increase in error rate was due to a configuration change elsewhere in the system.: The error rate spike was specific to service auth in region eu-west, not a system-wide issue. [E1, E2]

## Actions
- (corrective, high) Investigate the feature request R013 for any potential issues.
- (corrective, high) Review and test the configuration changes made to service auth in region eu-west.
- (preventive, medium) Monitor the service auth in region eu-west for any further issues.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth in region eu-west rose from 0.28% to 0.68% (+145%), with a change point at 2026-03-09T15:15:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth in region eu-west: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.26).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth in region eu-west stayed about the same (391 per 5 min before, 439 per 5 min after, +12%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth in region eu-west stayed about the same (90 ms before, 91 ms after, +0%).
- **E5** (record, tickets) Feature request: dark mode for the account page. (catalog, eu-west; 287 min before the change; record R013)
