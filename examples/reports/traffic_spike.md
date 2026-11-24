# INC-003: Why did the p95 latency go up on 21 March 2026?

## What changed
latency_p95_ms for region ap-south went from 136.3 to 241.7 (+77%) starting 2026-03-21T10:25:00Z. [E1, E2]

## Verdict: sufficient (score 0.85)
- A change event (tickets) matches the affected segment and timing (191 min before the change; matches the affected segment).

## Why it happened
1. **The flash sale campaign went live, causing a sudden increase in request volume and error rate.** (traffic, confidence 90%) [E5, E8]
   - Why: The marketing team launched a flash sale campaign in ap-south at 10:25 UTC, which is 191 minutes before the change.
   - Why: This campaign led to a significant increase in request volume and error rate in ap-south.
   - Why: The increase in requests overwhelmed the existing infrastructure, leading to higher latency and error rates.
2. **The help page typo caused a temporary spike in requests.** (traffic, confidence 70%) [E9, E8]
   - Why: The customer reported a typo on the help page, which caused a temporary increase in requests.
   - Why: This typo led to a temporary increase in request volume, contributing to the overall increase in latency and error rate.

## Ruled out
- The autoscaler was not configured correctly.: The autoscaler scaling out was the expected response to the increased traffic, and the evidence does not support any configuration issues. [E7]
- The help page typo caused a permanent increase in requests.: The help page typo was a one-time event and did not cause a sustained increase in requests. [E9]
- The search service was the root cause.: The search service did not show any significant changes in requests or error rates, and the evidence points to the flash sale campaign and autoscaler as the main contributors. [E3, E4, E5, E6, E7, E8]

## Actions
- (preventive, high) Review and optimize the autoscaler configuration to ensure it scales in a timely manner.
- (preventive, high) Implement a traffic management system to handle sudden spikes in traffic.
- (corrective, high) Fix the typo on the help page to prevent future temporary spikes in requests.

## Evidence
- **E1** (metric, metrics:latency_p95_ms) P95 latency for region ap-south rose from 136 ms to 242 ms (+77%), with a change point at 2026-03-21T10:25:00Z.
- **E2** (metric, metrics:latency_p95_ms) The change is concentrated in region ap-south: 4 of 12 service/region segments changed; the other segments stayed flat (largest after/before ratio 1.01).
- **E3** (metric, metrics:requests) At the same time, request volume for region ap-south rose (1234 per 5 min before, 4642 per 5 min after, +276%).
- **E4** (metric, metrics:error_rate) At the same time, error rate for region ap-south rose (0.35% before, 0.72% after, +109%).
- **E5** (record, tickets) Marketing: flash sale campaign goes live in ap-south at 10:25 UTC (ap-south; 191 min before the change; record R008)
- **E6** (record, alerts) Request volume 3x normal in ap-south (ap-south; 12 min after the change; record R010)
- **E7** (record, logs) autoscaler: scaling out, 4 new instances requested (ap-south; 20 min after the change; record R011)
- **E8** (record, tickets) Customer reports a typo on the help page. (checkout, us-east; 178 min before the change; record R009)
- **E9** (record, tickets) Customer asks how to download an invoice. (search, us-east; 341 min before the change; record R007)
