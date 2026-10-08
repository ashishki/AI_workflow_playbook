# Release 2.8 gate decision

**HOLD** for eu-central and eu-west as of 2026-10-08T12:00:00Z. All four independent gates fail; any one failure is sufficient to hold the release.

| Gate | Current finding | Blocking evidence |
| --- | --- | --- |
| Performance | eu-central checkout p95 rose from 200 to 234 ms (17%, 1,500 samples); eu-west refunds rose from 200 to 240 ms (20%, 1,500 samples). Both exceed 15%. | `perf-central-checkout` (11:00Z update), `perf-west-refunds` (10:00Z update) |
| Incidents | Open P1 checkout incident in eu-central and open P1 refunds incident in eu-west. | `INC-210`, `INC-211` (09:00Z updates) |
| Safety | `eu-central:recovery` and `eu-west:audit` are explicitly unverified. Central audit and west recovery are verified. No required check is absent. | `safe-central-recovery` (11:00Z update), `safe-west-audit` (10:00Z update) |
| Cost | Combined monthly projection is 112345.67 against budget 100000.00. In exact cents: 11,234,567 versus 10,000,000; the 110% ceiling is 11,000,000. Projection exceeds the ceiling by 234,567 cents and budget by 1,234,567 cents (`cost_delta_minor`). | `cost-target` (11:00Z update) |

## Conflicting and excluded records

Performance uses only release 2.8 in the target regions, measured status, measurement timestamps in the inclusive window 2026-10-07T12:00:00Z through 2026-10-08T12:00:00Z, and updates no later than assessment time. After filtering, the latest update per record ID wins. The central checkout 11:00Z regression supersedes its earlier 10% reading. The latest `perf-obsolete` reading is 205 ms (2.5%), superseding its old blocking reading. `perf-west-boundary` is exactly 15% and passes; `perf-low-sample` has only 999 samples and does not block. Stale measurements, future updates, estimates, other releases/regions and passing noise records contribute no blocking evidence.

Incidents discard future updates before deduplicating by incident ID. `INC-212` was resolved at 11:00Z, so its earlier open state does not block. `INC-213` is P2, `INC-214` concerns release 2.7, `INC-215` concerns search, `INC-216` concerns us-east and `INC-217` is a future update; none blocks this assessment. The other incident observations also fail the blocking criteria.

Safety discards future updates and takes the latest update per record ID, then the latest applicable record per target region/check for release 2.8. Central recovery's 11:00Z false result supersedes its 10:00Z true result. The future 13:00Z west audit verification is unavailable at assessment time, leaving the current false result. Release 2.7 checks cannot verify release 2.8.

Cost selects the latest current release 2.8 record covering exactly eu-central and eu-west. The 11:00Z projection supersedes the earlier 105000.00 projection; the release 2.7 cost record is excluded. Amounts are converted with the supplied `money_exact.to_minor_units`; integer comparisons preserve the strict threshold without float rounding. The 2026-10-06 legacy GO snapshot is historical and cannot override any current gate.

## Business impact and next safe action

Releasing would expose checkout and refunds to measured latency regressions and unresolved critical incidents, with incomplete audit/recovery assurance and spending above the allowed monthly ceiling. These synthetic sources do not quantify customer loss or establish a currency.

Keep release 2.8 on hold in both regions. Resolve `INC-210` and `INC-211`, remediate the latency regressions and collect qualifying measurements, verify central recovery and west audit for release 2.8, and bring the combined cost projection to at most 110% of budget. Reassess all four gates using updated current evidence at a new assessment time before release. No deployment or external contact was performed.
