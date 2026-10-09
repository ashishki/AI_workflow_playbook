# Release 2.8: HOLD

Assessment: 2026-10-08T12:00:00Z, for eu-central and eu-west. All four independent gates fail; any single failure requires HOLD. The machine-readable result is in [decision.json](decision.json).

| Gate | Current finding | Blocking evidence |
| --- | --- | --- |
| Performance | eu-central checkout p95 rises from 200 to 234 ms (17%); eu-west refunds rises from 200 to 240 ms (20%). Both have 1,500 samples and exceed the strict 15% threshold. | `perf-central-checkout`, `perf-west-refunds` in `data/performance.json` |
| Incidents | Open P1 checkout incident in eu-central and open P1 refunds incident in eu-west. | `INC-210`, `INC-211` in `data/incidents.csv` |
| Safety | eu-central recovery and eu-west audit are explicitly unverified. Central audit and west recovery are verified. | `safe-central-recovery`, `safe-west-audit` in `data/safety_cost.json` |
| Cost | Combined monthly projection is 112345.67 against budget 100000.00. The 110% ceiling is 110000.00; projection exceeds it by 2345.67. Projection minus budget is **1,234,567 cents**. Currency is unspecified. | `cost-target` in `data/safety_cost.json` |

Performance selection uses release 2.8, the two target regions, measured status, the inclusive measurement window 2026-10-07T12:00:00Z through assessment time, and updates no later than assessment. Eligible records are deduplicated by latest update per record ID before evaluating. Central checkout's 11:00 update (234 ms) replaces its 10:00 value (220 ms). `perf-obsolete` is now 205 ms at 11:00, superseding its older 400 ms reading. `perf-west-boundary` is exactly 15% and passes; `perf-low-sample` has only 999 samples. Stale measurements, future updates, estimated readings, other releases/regions and nonblocking noise contribute no evidence IDs.

Incidents discard future updates and then select the latest update per incident ID. `INC-212` was resolved at 11:00, superseding its earlier open status. `INC-217` has only a 13:00 update and is excluded. P2 incidents, search incidents and other releases/regions do not block.

Safety records discard future updates and are deduplicated by record ID; the latest applicable release-2.8 record then determines each region/check. Central recovery's 11:00 false replaces its 10:00 true. West audit's 13:00 true record is future and cannot override its current 10:00 false. Both missing-check entries denote unverified records, not absent records; their actual record IDs are included as evidence.

For exactly the two target regions, the current 11:00 `cost-target` projection replaces the earlier 08:00 projection of 105000.00. Release-2.7 cost records are excluded. Frozen `money_exact.py` converts decimal amount strings to integer cents; the exact comparison is `10 * 11234567 > 11 * 10000000`. No binary float or rounded percentage determines either threshold; equality passes. The 2026-10-06 legacy GO snapshot predates these sources and has no authority over this assessment.

These synthetic records indicate slower checkout/refunds paths, unresolved critical service faults, incomplete audit/recovery assurance and spending above the allowed ceiling. They do not establish actual customer impact or realized spending.

The next safe action is to keep release 2.8 on hold in both regions. Address the two open P1 incidents and latency regressions, obtain verified central recovery and west audit records, and reduce or revise the projection within the existing cost gate. Reassess all four gates together using fresh applicable evidence at a new assessment time before considering release. No contacts, deployment or external account actions were taken.
