# INC-019: Why did the error rate go up on 03 March 2026?

## What changed
error_rate for service auth went from 0.003904 to 0.05058 (+1196%) starting 2026-03-03T06:55:00Z. [E1, E2]

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
1. **The auth feature flag change increased error rate.** (config_change, confidence 90%) [E5]
   - Why: The auth feature flag was changed to 50% in eu-west.
   - Why: This change affected the error rate for service auth.
   - Why: The error rate increased from 0.39% to 5.06%.
   - Why: evidence_ids_supporting_chain_of_causes_and_confidence_in_cause_0.9_012_02
   - Why: evidence_ids_supporting_chain_of_causes_and_confidence_in_cause_0.9_012_02
2. **Upstream identity-db service failure caused the error rate increase.** (dependency, confidence 80%) [E6]
   - Why: The upstream identity-db service returned HTTP 503 for auth.
   - Why: This caused the auth service to timeout and fail.
   - Why: The auth service then had a higher error rate.
   - Why: evidence_ids_supporting_chain_of_causes_and_confidence_in_cause_0.8_014_02
   - Why: evidence_ids_supporting_chain_of_causes_and_confidence_in_cause_0.8_014_02

## Ruled out
- The increase in request volume caused the error rate increase.: The request volume for service auth stayed about the same. [E3]
- The increase in p95 latency caused the error rate increase.: The p95 latency for service auth rose, but the error rate increased more. [E4]
- The log error messages were the root cause.: The log error messages occurred after the change and are symptoms, not causes. [E7, E8, E9]

## Actions
- (corrective, high) Roll back the auth feature flag change to 50% and monitor the error rate.
- (preventive, high) Monitor the upstream identity-db service and ensure it is stable.
- (preventive, medium) Review and optimize the error handling in the auth service.

## Fact-check
- Evidence IDs cited by the model: 7, invented (removed): 0
- Factors dropped (no real evidence, or symptoms only): 0

## Evidence
- **E1** (metric, metrics:error_rate) Error rate for service auth rose from 0.39% to 5.06% (+1196%), with a change point at 2026-03-03T06:55:00Z.
- **E2** (metric, metrics:error_rate) The change is concentrated in service auth: 3 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.06).
- **E3** (metric, metrics:requests) At the same time, request volume for service auth stayed about the same (1082 per 5 min before, 1303 per 5 min after, +20%).
- **E4** (metric, metrics:latency_p95_ms) At the same time, p95 latency for service auth rose (91 ms before, 162 ms after, +79%).
- **E5** (record, config_changes) Changed auth feature flag new_ui_flow to 50% in eu-west (auth, eu-west; 2 min before the change; record R012; fit: right time and place: a strong candidate cause)
- **E6** (record, alerts) Upstream identity-db returning HTTP 503 for auth (auth; 5 min after the change; record R014; fit: right time and place: a strong candidate cause)
- **E7** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, ap-south; 1 min after the change; record R013; fit: describes a symptom, not a change)
- **E8** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, us-east; 7 min after the change; record R015; fit: after the change, so a symptom, not a cause)
- **E9** (record, logs) auth: ERROR upstream identity-db timeout after 3 retries (auth, eu-west; 15 min after the change; record R016; fit: after the change, so a symptom, not a cause)
