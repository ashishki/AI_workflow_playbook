# Release 2.8: HOLD

As of **2026-10-08T12:00:00Z**, release 2.8 must be held for eu-central and
eu-west. All four independent gates fail; any one failure is sufficient to hold
the combined release. The machine-readable result is in [decision.json](decision.json).

| Gate | Current blocking findings | Evidence in current sources |
| --- | --- | --- |
| Performance | eu-central checkout: 200 → 234 ms p95, a 17% regression; eu-west refunds: 200 → 240 ms, a 20% regression. Both have 1,500 samples. | `data/performance.json`: `perf-central-checkout` (11:00Z update), `perf-west-refunds` (10:00Z update). |
| Incidents | Open P1 checkout incident in eu-central and open P1 refunds incident in eu-west. | `data/incidents.csv`: `INC-210`, `INC-211` (09:00Z updates). |
| Safety | eu-central recovery and eu-west audit are explicitly false, so unverified. Central audit and west recovery are true. No required check is absent. | `data/safety_cost.json`: `safe-central-recovery` (11:00Z), `safe-west-audit` (10:00Z). |
| Cost | Combined monthly projection is 112,345.67 against a 100,000.00 budget; the 110% ceiling is 110,000.00. | `data/safety_cost.json`: `cost-target` (11:00Z update). |

Cost was converted exactly from decimal strings to integer cents using the frozen
`money_exact.to_minor_units` helper. Projection is 11,234,567 cents; budget is
10,000,000 cents. The budget delta is **1,234,567 cents**, and the projection
exceeds the ceiling by **234,567 cents**. The strict test is
`11,234,567 × 100 > 10,000,000 × 110`; no float rounding is used.

## Resolving conflicting and stale records

Performance records were first filtered to release 2.8, the two target regions,
measured status, the inclusive measurement window
2026-10-07T12:00:00Z–2026-10-08T12:00:00Z, and updates no later than assessment.
Eligible records were then deduplicated by record ID, keeping the latest update.
The 11:00Z central checkout value supersedes its earlier passing 220 ms value.
`perf-obsolete` now passes at 205 ms, superseding its earlier 400 ms value.
`perf-west-boundary` is exactly 15% and passes; `perf-low-sample` has only 999
samples and does not block. `perf-stale` is outside the measurement window,
`perf-future` is updated after assessment, and `perf-estimate` is not measured.
Other releases/regions and passing noise records contribute no evidence IDs.

Incidents were filtered for current updates, deduplicated by incident ID, and then
checked for target release/regions, open P1 status and checkout/refunds service.
`INC-212` is resolved in its latest 11:00Z update, so its earlier open state does
not block. `INC-213` is P2, `INC-214` is release 2.7, `INC-215` affects search,
`INC-216` affects us-east, and `INC-217` has only a future update; all are excluded.

Safety/cost records were filtered for current updates and deduplicated by record
ID. The latest applicable safety record was then selected for each target
region/check on release 2.8. The false 11:00Z central recovery update supersedes
the true 10:00Z update. `safe-west-audit-future` cannot override the current false
audit result. Older-release safety records cannot verify release 2.8.
The latest applicable combined cost record is `cost-target` at 11:00Z, replacing
the passing 08:00Z projection of 105,000.00. `cost-old-version` is release 2.7.

The 2026-10-06 `data/legacy_snapshot.json` GO assessment is historical and cannot
override these current records. Only the seven actual blocking IDs appear in
`evidence_ids`; no IDs are invented for absent checks.

## Business impact and next safe action

The records indicate slower checkout/refund journeys, unresolved critical service
incidents, unverified recovery/audit safeguards, and monthly spending above the
allowed ceiling. These are synthetic operational findings; actual customer harm
or realized spending has not been observed.

Keep release 2.8 on hold for both regions. Before reassessment, address the two
latency regressions and capture fresh qualifying measurements, resolve the two
P1 incidents with current status records, verify central recovery and west audit,
and bring the combined projection to at most 110% of budget. Reevaluate all four
gates using fresh records and the new assessment cutoff. No contact, deployment,
external account access, or source-data changes were performed.
