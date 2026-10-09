# Release 2.8 gate decision

**HOLD** for eu-central and eu-west as of 2026-10-08T12:00:00Z. All four independent gates fail; any one failure is sufficient to hold the release. The machine-readable result is in decision.json.

| Gate | Current finding and blocking evidence |
| --- | --- |
| Performance | In data/performance.json, `perf-central-checkout` increases p95 from 200 to 234 ms (17%) in eu-central; `perf-west-refunds` increases it from 200 to 240 ms (20%) in eu-west. Each has 1,500 samples, exceeding the 1,000-sample minimum, and each regression is strictly above 15%. |
| Incidents | In data/incidents.csv, `INC-210` is an open P1 checkout incident in eu-central; `INC-211` is an open P1 refunds incident in eu-west. Both apply to release 2.8. |
| Safety | In data/safety_cost.json, `safe-central-recovery` and `safe-west-audit` are false. The missing/unverified checks are `eu-central:recovery` and `eu-west:audit`. Central audit and west recovery are verified. |
| Cost | In data/safety_cost.json, the current combined two-region `cost-target` projects 112345.67 against a 100000.00 monthly budget. In exact cents, projection is 11,234,567, budget is 10,000,000, and delta is +1,234,567. The 110% ceiling is 11,000,000 cents; projection exceeds it by 234,567 cents. |

Records updated after the assessment time were discarded. Performance records were first restricted to release 2.8, the two target regions, measured status, and the inclusive measurement window 2026-10-07T12:00:00Z through 2026-10-08T12:00:00Z, then deduplicated by record_id using the latest eligible update. Incidents and safety/cost records were deduplicated by their IDs after the future-update cutoff; latest applicable safety records were then selected per region/check, and the latest cost record required exactly the two target regions. All comparisons used exact arithmetic.

The 11:00 update of `perf-central-checkout` replaces its earlier passing value. The latest `perf-obsolete` value passes, replacing its older blocking value. `perf-west-boundary` is exactly 15% and passes; `perf-low-sample` has only 999 samples and cannot block. Stale measurements, future updates, estimated status, other releases/regions and nonblocking noise are excluded.

`INC-212` was resolved at 11:00, superseding its earlier open status. Future `INC-217`, P2 incidents and incidents for other services/releases/regions do not block. Central recovery's false 11:00 update supersedes its true 10:00 update; the true west audit record at 13:00 is future data and cannot clear the current false check. The 11:00 `cost-target` projection supersedes its 08:00 value; release 2.7 cost records are excluded. The GO assessment in data/legacy_snapshot.json is from October 6 and cannot override these current sources. Evidence IDs contain only the seven actual blockers above, with no legacy or excluded records.

Proceeding would expose checkout/refunds to elevated latency and active critical faults, leave recovery/audit assurance incomplete, and exceed the permitted monthly cost ceiling. The next safe action is to keep release 2.8 on hold in both regions, address the latency regressions and P1 incidents, verify central recovery and west audit, and reduce the combined projection to at most 110% of budget. Then reassess all four gates against fresh current records before proceeding. These are synthetic findings; no deployment, contact or external action was performed.
