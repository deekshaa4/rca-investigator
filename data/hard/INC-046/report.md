# INC-046: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service checkout, region ap-south went from 0.005281 to 0.03543 (+571%) starting 2026-03-26T06:10:00Z. [E1, E2]

## Verdict: sufficient (score 1.00)
- ✓ A change event (deploys) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✓ No competing change event fits as well.
- ✓ The main factor rests on this event.

## Why it happened
1. **New deployment of checkout v3.17 caused the error rate to spike.** (deployment, confidence 90%) [E5, E7, E8, E9]
   - Why: Checkout v3.17 deployment introduced a new version of the RequestHandler.
   - Why: NullPointerException in RequestHandler.serialize (v3.17) led to increased error rate.
   - Why: Error rate rose from 0.53% to 3.54% on 26 March 2026.

## Ruled out
- The error rate increase was due to a sudden surge in user traffic.: Request volume and p95 latency remained stable before and after the change. [E3, E4]
- The error rate increase was caused by a configuration change.: No evidence supports a config change leading to the error rate increase. [E1, E2, E3, E4]
- The error rate increase was due to a dependency issue with an external service.: No evidence supports a dependency issue leading to the error rate increase. [E1, E2, E3, E4]

## Actions
- (corrective, high) Fix the NullPointerException in RequestHandler.serialize (v3.17) in checkout v3.17.
- (preventive, medium) Monitor and log RequestHandler.serialize (v3.17) for any future occurrences.
- (preventive, high) Review and test the new checkout v3.17 in a staging environment before production deployment.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region ap-south rose from 0.53% to 3.54% (+571%), with a change point at 2026-03-26T06:10:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.05).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region ap-south stayed about the same (168 per 5 min before, 198 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region ap-south stayed about the same (221 ms before, 220 ms after, -0%).
- **E5** (record, deploys) Deployed checkout v3.17 to ap-south (checkout, ap-south; 2 min before the change; record R010)
- **E6** (record, alerts) High error rate on checkout in ap-south (checkout, ap-south; 10 min after the change; record R011)
- **E7** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 10 min after the change; record R012)
- **E8** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 28 min after the change; record R013)
- **E9** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 36 min after the change; record R014)
