# Test-First Paired Pilot Results

Record date: 2026-07-15
Status: `adjudicated - no empirical improvement claim supported`
Pilot plan: `docs/evaluation/TEST_FIRST_PILOT_PLAN.md`
Frozen candidate registry: `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
Static preflight: `reports/test_first_pilot/shishki_bot_v1/PREFLIGHT_2026-07-15.md`
Completed run root: `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/`
Blind review packages: `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/blind_review/`
Protected mapping: `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/protected_mapping/mapping.json`
Adjudication report: `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/adjudication_report.json`
Valid real-model pilot runs: 12 machine-valid
Valid paired units: 6 prepared; 6 adjudicated
Empirical improvement claims: none

## Decision

Adoption decision: `rejected` for promoting the test-first additions as
empirically better or default based on TFA-7.

The existing workflow is not expanded by this pilot. The documented test-first
protocol remains a governance and evidence pattern under existing risk routing,
but TFA-7 does not support a claim that the test-first condition improves
quality, reliability, repair time, or productivity. A future improvement claim
requires a larger preregistered pilot with independent role separation, more
tasks/repositories, and a precision or power rationale.

## Readiness Result

| Required input | Recorded state | Gate |
|----------------|----------------|------|
| Human-approved real repository snapshots | approval copied into completed run; SHA-256 `cc5aaac2358bde065c4300c54687f39dc606838b70e8ce27b8e359d27f71c444` | met |
| Project-specific task fixtures | two sparse real-task RED fixtures frozen in `shishki_bot_ci_v1` | met |
| Frozen baseline/test-first prompt bundles | four prompts present; identical task facts checked | met |
| Independent project scorers and expected failure taxonomy | public shell/diff/file scorers frozen and smoke-checked | met |
| Protected holdout setup where routed | not required by either frozen route | not applicable |
| External append-only event ledger | 12 arm ledgers validated by review preparer | met |
| External runner and subscription-backed execution approval | guarded runner completed once from external shell | met |
| Provider/model/parameter registry | Codex CLI `0.144.4`, `gpt-5.6-sol`, medium/default frozen | met |
| Approved paired budget | exactly 12 subscription-backed Codex executions, zero retries, USD 0 paid API | met |
| Repository data/redaction/retention approval | minimized public boundary and 90/365 proposal recorded in approval | met |
| Real-model command receipts and bundles | 12 bundles; each has 2 command receipts and validates with zero errors/warnings | met |

The `codex` executable is logged in through ChatGPT and the companion CLI is
installed locally, but tool availability is not approval to spend subscription
quota or access the frozen fixture. The guarded runner rejects a nested Codex
run from the active session. Static preflight for manifest
`38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3`
passed with zero model invocations. The completed real run is sealed by
`COMPLETED_RUN.json` with SHA-256
`cfd36c215be25c3baa6740c888ccb1a53d6bafca1e9e40f4c861c7b3e4a61136`.

## Pilot Metrics

| Metric family | Numerator | Denominator | Result |
|---------------|-----------|-------------|--------|
| Public and holdout pass | 12 machine pass | 12 pilot trials | `machine_pass_before_adjudication` |
| Mutation and property oracles | not observed | 0 applicable pilot trials | `not_measured` |
| Critic false alarms/misses/calibration | not observed | 0 critic-calibration cases | `not_measured` |
| Repair turns and time to green | process telemetry joined after unblinding | 12 event ledgers | `baseline fewer verifier attempts/failures in this pilot` |
| Rollback/reopen | not observed | 0 eligible merges | `not_observed` |
| UI behavior/visual defects | not observed | 0 routed UI pilot trials | `not_applicable` |
| Cost, tokens, latency, and intervention | traces captured; exact provider tokens unavailable | 12 pilot attempts | `tokens/cost unknown; human intervention false in mapping` |

Blind adjudication admitted all six pairs. Preferences joined to the protected
mapping produced baseline 2 wins, playbook 1 win, and 3 ties. Both conditions
satisfied the rubric in all admitted pairs, and the blind review recorded 0
blinding leaks. The protected mapping SHA is
`b4f525d1b7d928386f09e608d79f67ce369159c8029375e3bd2785fdcb5879e4`; the
adjudication report records the frozen review digests and completed-run seal.

Per-pair outcome:

| Pair | Task | Trial | A condition | B condition | Blind preference | Condition outcome |
|------|------|-------|-------------|-------------|------------------|-------------------|
| pair-001 | pin_ci_actions | 0 | playbook | baseline | tie | tie |
| pair-002 | pin_ci_actions | 1 | playbook | baseline | tie | tie |
| pair-003 | pin_ci_actions | 2 | baseline | playbook | tie | tie |
| pair-004 | reject_unapproved_ci_actions | 0 | playbook | baseline | B | baseline |
| pair-005 | reject_unapproved_ci_actions | 1 | baseline | playbook | A | baseline |
| pair-006 | reject_unapproved_ci_actions | 2 | baseline | playbook | B | playbook |

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
| Pilot command receipts, bundles, or equivalent artifacts | met | 12 validated real-model bundles under completed run root |
| Results include wins and failures | met | six blind pair reports frozen and joined to protected mapping |
| Final adoption decision recorded | met | `rejected` for empirical/default promotion from this pilot |
| Follow-up tasks created for gaps | met | TFA-7.3 records the larger-pilot requirement before any improvement claim |

TFA-7.2 is complete for the `shishki-tfa7-20260715` pilot. The result is a
negative claim-control result: it prevents a TDD/test-first improvement claim
from this evidence rather than proving the opposite.

## Resume Conditions

Future pilots must repeat the same sequence: freeze blind reports before opening
the protected mapping, then have a custodian/adjudicator join the labels and
record an adoption decision. Any missing review, mapping access by the reviewer
before freeze, version drift, invalid call, or unmet denominator remains
`inconclusive`; no extra call is permitted without a new approved budget.
