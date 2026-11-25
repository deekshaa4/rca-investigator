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
1. **New deployment of checkout v3.17 introduced a NullPointerException in RequestHandler.serialize.** (deployment, confidence 90%) [E5, E6, E7, E8, E9]
   - Why: Checkout v3.17 was deployed to ap-south 2 minutes before the error rate spike.
   - Why: NullPointerException in RequestHandler.serialize was observed in the logs 10 minutes after the deployment.
   - Why: The error rate increased from 0.53% to 3.54% after the deployment.
   - Why: evidence_ids
2. **The error rate spike coincided with a deployment, suggesting a correlation.** (unknown, confidence 80%) [E5]
   - Why: The error rate spike occurred at the same time as a deployment (checkout v3.17).
   - Why: No other deployment was noted in the same region at the same time.
   - Why: The error rate spike was not preceded by any other known changes or anomalies.
   - Why: evidence_ids

## Ruled out
- The increase in error rate was due to a sudden increase in user traffic.: The request volume and p95 latency did not change significantly. [E3, E4]
- The increase in error rate was due to a configuration change.: No configuration change was noted in the evidence. []
- The increase in error rate was due to a dependency issue with an external service.: No external service issues were noted in the evidence. []

## Actions
- (corrective, high) Rollback the checkout v3.17 deployment to ap-south.
- (preventive, high) Implement a robust error handling mechanism in the RequestHandler.serialize method.
- (preventive, medium) Monitor the RequestHandler.serialize method for similar issues in future deployments.

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service checkout in region ap-south rose from 0.53% to 3.54% (+571%), with a change point at 2026-03-26T06:10:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service checkout in region ap-south: 1 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.05).
- **E3** (metric, metrics:requests) At the same time, request volume for service checkout in region ap-south stayed about the same (168 per 5 min before, 198 per 5 min after, +18%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service checkout in region ap-south stayed about the same (221 ms before, 220 ms after, -0%).
- **E5** (record, deploys) Deployed checkout v3.17 to ap-south (checkout, ap-south; 2 min before the change; record R010; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) High error rate on checkout in ap-south (checkout, ap-south; 10 min after the change; record R011; fit: after the change, so a symptom, not a cause)
- **E7** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 10 min after the change; record R012; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 28 min after the change; record R013; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) checkout: ERROR NullPointerException in RequestHandler.serialize (v3.17) (checkout, ap-south; 36 min after the change; record R014; fit: after the change, so a symptom, not a cause)
