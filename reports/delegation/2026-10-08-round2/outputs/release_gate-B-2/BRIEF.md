# Release 2.8: HOLD

Assessment: 2026-10-08T12:00:00Z, covering eu-central and eu-west. All four independent gates fail; any one failure is sufficient to HOLD the combined release.

| Gate | Finding | Blocking evidence |
| --- | --- | --- |
| Performance | eu-central checkout p95 rises from 200 to 234 ms (17%); eu-west refunds rises from 200 to 240 ms (20%). Each has 1,500 samples and exceeds the strict 15% limit. | `data/performance.json`: `perf-central-checkout` (11:00 update), `perf-west-refunds` (10:00 update) |
| Incidents | Two latest open P1 incidents affect checkout in eu-central and refunds in eu-west. | `data/incidents.csv`: `INC-210`, `INC-211` (09:00 updates) |
| Safety | eu-central recovery and eu-west audit are explicitly unverified. eu-central audit and eu-west recovery are verified. No required check is absent. | `data/safety_cost.json`: `safe-central-recovery` (11:00 update), `safe-west-audit` (10:00 update) |
| Cost | Combined monthly projection is 112345.67 against a 100000.00 budget. This exceeds the 110000.00 gate threshold by 2345.67. Projection minus budget is exactly **1,234,567 cents**. | `data/safety_cost.json`: `cost-target` (11:00 update) |

Performance selection uses release 2.8, the two target regions, measured status, the inclusive measurement window 2026-10-07T12:00:00Z through assessment time, and updates no later than assessment. Latest updates per record ID leave 29 eligible records. `perf-central-checkout` at 11:00 supersedes the earlier 10% result. `perf-obsolete` at 11:00 supersedes its earlier regression and passes at 2.5%. `perf-west-boundary` passes at exactly 15%; `perf-low-sample` cannot block with 999 samples. Stale measurements, future updates, estimates and other releases/regions are excluded. Eligible noise measurements remain below the threshold.

Incidents discard future updates before deduplication by incident ID. `INC-212` is resolved by its 11:00 update, superseding its earlier open state. `INC-213` is P2; `INC-214` concerns release 2.7; `INC-215` concerns search; `INC-216` concerns us-east; `INC-217` has only a future update. None blocks this assessment. The remaining background incidents also fail the blocking criteria.

Safety discards future updates, deduplicates record IDs and selects the latest applicable release 2.8 record per region/check. The 11:00 false recovery result supersedes the earlier true result for eu-central. `safe-west-audit-future` at 13:00 cannot override the current false audit result. Release 2.7 safety records provide no verification for release 2.8.

Cost uses the latest current record covering exactly both target regions. The 11:00 `cost-target` replaces its 08:00 projection of 105000.00; `cost-old-version` is excluded. Amounts are converted to integer cents with the frozen `money_exact.py` helper; the threshold comparison is exactly `11234567 * 10 > 10000000 * 11`, without floating-point rounding. Equality at 110% would pass. The 2026-10-06 legacy GO snapshot is historical and cannot override these current sources. Only the seven actual blocking IDs appear in `decision.json`.

The recorded latency regressions and open P1 incidents expose checkout and refunds to service degradation in both regions. The failed safety checks leave audit/recovery readiness unverified, and the projection exceeds the allowed cost envelope. These are synthetic findings; no actual customer impact is established.

The next safe action is to retain the release hold, remediate the latency regressions and qualifying incidents, obtain verified recovery/audit results, and bring the combined projection within 110% of budget. Then reassess all four gates from fresh records at a new explicit assessment time. No contact or deployment was performed.
