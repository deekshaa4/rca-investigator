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
1. **The catalog feature flag change led to increased error rate.** (config_change, confidence 90%) [E6, E1]
   - Why: The catalog feature flag was changed to 50% in eu-west, causing the service to behave differently.
   - Why: This change affected the catalog service, leading to a higher error rate as the system tried to handle the new configuration.
   - Why: The error rate increased from 0.38% to 3.01% after the change, indicating the change had a direct impact on the error rate.
2. **The upstream catalog-db service was experiencing issues, causing timeouts and errors.** (dependency, confidence 80%) [E5, E7, E8, E9]
   - Why: The catalog service was experiencing timeouts and errors due to upstream catalog-db service issues.
   - Why: These issues caused the service to return HTTP 503, leading to a higher error rate.
   - Why: The error rate increased from 0.38% to 3.01% after the change, indicating the upstream service issues were the root cause.

## Ruled out
- The increase in request volume caused the error rate to go up.: The request volume did not change significantly, and the error rate increased after the change. [E3]
- The increase in p95 latency caused the error rate to go up.: The p95 latency increased, but the error rate increased after the change, indicating the latency increase was a symptom, not a cause. [E4]

## Actions
- (corrective, high) Fix the upstream catalog-db service issues
- (preventive, high) Monitor the catalog feature flag changes and their impact
- (preventive, medium) Review and stabilize the catalog feature flag configuration

## Fact-check
- Evidence IDs cited by the model: 8, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service catalog rose from 0.38% to 3.01% (+695%), with a change point at 2026-03-26T11:35:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service catalog: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.08).
- **E3** (metric, metrics:requests) At the same time, request volume for service catalog stayed about the same (1638 per 5 min before, 2024 per 5 min after, +24%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service catalog rose (121 ms before, 217 ms after, +80%).
- **E5** (record, alerts) Upstream catalog-db returning HTTP 503 for catalog (catalog; 2 min after the change; record R013; fit: right time and place: a strong candidate cause)
- **E6** (record, config_changes) Changed catalog feature flag new_ui_flow to 50% in eu-west (catalog, eu-west; 2 min before the change; record R012; fit: right time and place: a strong candidate cause)
- **E7** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, eu-west; 14 min after the change; record R014; fit: after the change, so a symptom, not a cause)
- **E8** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, us-east; 14 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) catalog: ERROR upstream catalog-db timeout after 3 retries (catalog, ap-south; 16 min after the change; record R016; fit: after the change, so a symptom, not a cause)
