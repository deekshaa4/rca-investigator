# INC-044: Why did the error rate go up on 26 March 2026?

## What changed
error_rate for service catalog went from 0.003782 to 0.03005 (+695%) starting 2026-03-26T11:35:00Z. [E1, E2]

## Verdict: partial (score 0.90)
- ✓ A change event (config_changes) lines up in time (2 min before the change).
- ✓ It concerns the affected service/region.
- ✓ 4 log/alert record(s) after the change agree with the numbers.
- ✓ Request volume stayed steady, ruling out a traffic spike.
- ✗ 1 other change event(s) fit about as well.
- ✓ The main factor rests on this event.
- ✗ Two or more changes fit equally well, so the cause cannot be confirmed.
- Data that would help: Details to tell the competing changes apart (e.g. a rollback test)

## Why it happened
1. **The service catalog feature flag change likely caused the error rate to increase.** (config_change, confidence 90%) [E6, E1]
   - Why: The catalog feature flag was changed to 50% in eu-west, which could have affected the service catalog's functionality.
   - Why: The change in the feature flag led to a different behavior of the service catalog, possibly causing more errors.
   - Why: The error rate increased from 0.38% to 3.01%, indicating that the change in the feature flag had a significant impact on the service catalog's performance.
2. **The upstream catalog-db service was experiencing issues, contributing to the error rate increase.** (dependency, confidence 80%) [E5, E7, E8, E9]
   - Why: The catalog-db service returned HTTP 503 (Service Unavailable) for the catalog, indicating a failure.
   - Why: The service catalog experienced a timeout after 3 retries, suggesting that the upstream catalog-db service was the bottleneck.
   - Why: The error rate increase and the timeout issues are likely caused by the failure of the upstream catalog-db service.

## Ruled out
- The increase in request volume caused the error rate to rise.: The request volume for service catalog did not change significantly, and the error rate increase is more pronounced than the increase in request volume. [E3]
- The increase in p95 latency caused the error rate to rise.: The p95 latency increased by 80%, but the error rate increased by 695%, suggesting that other factors were more significant. [E4]

## Actions
- (corrective, high) Investigate and fix the upstream catalog-db service issues.
- (preventive, medium) Monitor the feature flag changes and their impact on service catalog.
- (preventive, medium) Review and potentially revert the feature flag change if necessary.

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.38% to 3.01% (+695%), with a change point at 2026-03-26T11:35:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1638 per 5 min before, 2024 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (121 ms before, 217 ms after, +80%).
- **E5** (record, alerts) Upstream catalog-db returning HTTP 503 for catalog (catalog; 2 min after the change; record R013)
- **E6** (record, config_changes) Changed catalog feature flag new_ui_flow to 50% in eu-west (catalog, eu-west; 2 min before the change; record R012)
- **E7** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 14 min after the change; record R014)
- **E8** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 14 min after the change; record R015)
- **E9** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, ap-south; 16 min after the change; record R016)
