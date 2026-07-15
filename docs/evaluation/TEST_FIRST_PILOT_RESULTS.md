# Test-First Paired Pilot Results

Record date: 2026-07-15
Status: `blocked - not run`
Pilot plan: `docs/evaluation/TEST_FIRST_PILOT_PLAN.md`
Frozen candidate registry: `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
Static preflight: `reports/test_first_pilot/shishki_bot_v1/PREFLIGHT_2026-07-15.md`
Valid real-model pilot runs: 0
Valid paired units: 0
Empirical improvement claims: none

## Decision

Adoption decision: `not eligible - deferred`.

This is not one of the final adoption outcomes (`default`, `Strict-only`,
`optional`, or `rejected`) because no paired real-project evidence exists. The
existing workflow remains unchanged. A human adoption authority must choose a
final outcome only after the TFA-7.2 acceptance criteria are met; missing
evidence cannot be treated as a negative or positive result.

## Readiness Result

| Required input | Recorded state | Gate |
|----------------|----------------|------|
| Human-approved real repository snapshots | `shishki_bot` exact bases selected; approval pending | blocked |
| Project-specific task fixtures | two sparse real-task RED fixtures frozen in `shishki_bot_ci_v1` | prepared, approval blocked |
| Frozen baseline/test-first prompt bundles | four prompts present; identical task facts checked | prepared, approval blocked |
| Independent project scorers and expected failure taxonomy | public shell/diff/file scorers frozen and smoke-checked | prepared, critic/approval blocked |
| Protected holdout setup where routed | not required by either frozen route | not applicable |
| External append-only event ledger | `test_first_pilot.event.v1` adapter events frozen; richer trace-derived metrics remain unknown | prepared, approval blocked |
| External runner and subscription-backed execution approval | guarded external runner and completed-run seal present; execution approval absent | blocked |
| Provider/model/parameter registry | Codex CLI `0.144.4`, `gpt-5.6-sol`, medium/default frozen | prepared, approval blocked |
| Approved paired budget | proposed exactly 12 subscription-backed Codex executions and USD 0 paid API; internal inference count is unbounded; not approved | blocked |
| Repository data/redaction/retention approval | minimized public boundary and 90/365 proposal recorded; not approved | blocked |
| Real-model command receipts and bundles | none | blocked |

The `codex` executable is logged in through ChatGPT and the companion CLI is
installed locally, but tool availability is not approval to spend subscription
quota or access the frozen fixture. The guarded runner rejects a nested Codex
run from the active session. Static preflight for manifest
`38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3`
passed with zero model invocations.

## Pilot Metrics

| Metric family | Numerator | Denominator | Result |
|---------------|-----------|-------------|--------|
| Public and holdout pass | not observed | 0 pilot trials | `not_measured` |
| Mutation and property oracles | not observed | 0 applicable pilot trials | `not_measured` |
| Critic false alarms/misses/calibration | not observed | 0 adjudicated pilot cases | `not_measured` |
| Repair turns and time to green | not observed | 0 event ledgers | `unknown` |
| Rollback/reopen | not observed | 0 eligible merges | `not_observed` |
| UI behavior/visual defects | not observed | 0 routed UI pilot trials | `not_applicable_to_current_empty_set` |
| Cost, tokens, latency, and intervention | not observed | 0 pilot attempts | `unknown` |

There are no pilot wins or failures to report. Reporting the absence explicitly
is preferable to reclassifying scripted mechanism behavior as project evidence.

## Excluded Mechanism Evidence

The pre-existing `playbook_core_v1` artifact set contains five scripted
baseline bundles and five scripted Playbook bundles, one trial per condition and
task. All ten bundles validate, but the adapter is scripted, the tasks are
generic mechanism fixtures, and the comparison records a per-task stability
warning. Its own status is "mechanism demonstration, not empirical proof of
Playbook effectiveness."

These artifacts are excluded from every pilot numerator and denominator:

- suite manifest SHA-256:
  `4c7b8de8b6bc4487a1c7e742719c1e7ab05006cf9eca9e031c888c313f127ecc`
- mechanism comparison SHA-256:
  `8fdfb86e7f16960dfe854413889f9c33466ce26575450e5f5e1ce9dc10e2bb1a`
- validation record: `reports/test_first_pilot/PREFLIGHT_NOT_RUN.md`

## Acceptance State

| TFA-7.2 acceptance criterion | State | Evidence |
|-------------------------------|-------|----------|
| Pilot command receipts, bundles, or equivalent artifacts | not met | no real-project command run |
| Results include wins and failures | not met | zero valid pilot runs |
| Final adoption decision recorded | not met | decision is not eligible and deferred |
| Follow-up tasks created for gaps | met | TFA-7.2A through TFA-7.2C in `docs/tasks.md` |

TFA-7.2 remains blocked. The document is a durable negative preflight record,
not a claim that the pilot task is complete.

## Resume Conditions

Resume TFA-7.2 only after the named owners approve TFA-7.1 plus TFA-7.2A through
TFA-7.2C and the final execution gate, citing the current manifest and fresh
critic digests. A human then launches `tools/run_test_first_pilot.sh` from an
external shell. Any version drift, invalid call, unmet denominator, or missing
review remains `inconclusive`; no extra call is permitted under the proposed
zero-retry budget.
