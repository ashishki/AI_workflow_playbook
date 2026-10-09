# Release 2.8: HOLD

Assessment: 2026-10-08T12:00:00Z; scope: eu-central and eu-west. All four independent gates fail. Hold the release in both regions.

| Gate | Current finding | Blocking evidence |
| --- | --- | --- |
| Performance | eu-central checkout p95 is 234 ms versus 200 ms (+17%); eu-west refunds is 240 ms versus 200 ms (+20%). Each has 1,500 samples and was measured at 09:00Z on October 8. | `data/performance.json`: `perf-central-checkout` (11:00Z update), `perf-west-refunds` (10:00Z update) |
| Incidents | Open P1 checkout incident in eu-central and open P1 refunds incident in eu-west. | `data/incidents.csv`: `INC-210`, `INC-211` (09:00Z updates) |
| Safety | eu-central recovery is unverified (false); eu-west audit is unverified (false). eu-central audit and eu-west recovery are verified. | `data/safety_cost.json`: `safe-central-recovery` (11:00Z update), `safe-west-audit` (10:00Z update) |
| Cost | Combined monthly projection 112345.67 versus budget 100000.00. The 110% cap is 110000.00, exceeded by 2345.67. Budget delta is +12345.67, exactly 1,234,567 cents. | `data/safety_cost.json`: `cost-target` (11:00Z update) |

## Resolving conflicting and stale records

Performance selection used release 2.8, the two target regions, measured status, the inclusive measurement window 2026-10-07T12:00:00Z through 2026-10-08T12:00:00Z, and updates no later than assessment. Selected records were deduplicated by record_id using the latest update before evaluation. The 11:00Z central checkout update supersedes the earlier 220 ms reading. The latest `perf-obsolete` reading is 205 ms, so its earlier 400 ms reading does not block. `perf-west-boundary` is exactly +15% and passes. `perf-low-sample` has only 999 samples; `perf-stale` is outside the measurement window; `perf-future` is updated after assessment; `perf-estimate` is not measured. Other releases/regions and passing observations add no blocking evidence.

Incident updates after assessment were discarded before deduplicating incident_id. `INC-212` was resolved at 11:00Z and does not block; `INC-217` is a future update. P2 incidents and incidents in other services, releases or regions were excluded.

Safety updates after assessment were discarded and record_id duplicates resolved before selecting the latest applicable record for each region/check. The 11:00Z false central recovery update supersedes the 10:00Z true update. The 13:00Z `safe-west-audit-future` verification cannot override the current false west audit. Both missing_safety_checks entries mean unverified, not absent records; their explicit IDs are available as evidence. Other versions/regions do not satisfy release 2.8 requirements.

The latest current cost record covers exactly eu-central and eu-west. Its 11:00Z projection supersedes the 08:00Z projection of 105000.00; `cost-old-version` is outside scope. Amounts were converted from decimal strings to integer cents with the supplied frozen `money_exact.to_minor_units`; the cap was compared by integer cross-multiplication, without floating-point rounding. The projection is 12.34567% above budget, strictly beyond the allowed 10%.

`data/legacy_snapshot.json` is an October 6 GO assessment. Current operational records supersede it; it supplies no blocking evidence.

## Business impact and next safe action

The release currently fails checkout/refunds latency requirements in both regions, has unresolved critical incidents in those flows, lacks required recovery/audit verification, and exceeds the combined monthly cost cap. The supplied records establish gate failures; they do not quantify customer loss or incident duration beyond recorded timestamps.

Keep release 2.8 on hold in both regions. Address the latency regressions and critical incidents, obtain current successful central recovery and west audit checks, and bring the combined projection within 110% of budget. Reassess all four gates using refreshed records at a new assessment time; GO requires every gate to pass. This exercise performs no deployment or external contact.
