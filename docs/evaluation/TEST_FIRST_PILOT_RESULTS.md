# Test-First Paired Pilot Results

Record date: 2026-07-15
Status: `run captured - blind adjudication pending`
Pilot plan: `docs/evaluation/TEST_FIRST_PILOT_PLAN.md`
Frozen candidate registry: `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
Static preflight: `reports/test_first_pilot/shishki_bot_v1/PREFLIGHT_2026-07-15.md`
Completed run root: `reports/test_first_pilot/shishki_bot_v1/runs/shishki-tfa7-20260715/`
Blind review packages: `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/blind_review/`
Protected mapping: `reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/protected_mapping/mapping.json`
Valid real-model pilot runs: 12 machine-valid
Valid paired units: 6 prepared; 0 adjudicated
Empirical improvement claims: none

## Decision

Adoption decision: `not eligible - blind adjudication pending`.

This is not one of the final adoption outcomes (`default`, `Strict-only`,
`optional`, or `rejected`) because the completed run still requires condition-
blind pair review and protected unblinding. The existing workflow remains
unchanged. A human adoption authority must choose a final outcome only after the
TFA-7.2 acceptance criteria are met; machine-valid bundles alone cannot be
treated as a positive workflow result.

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
| Critic false alarms/misses/calibration | not observed | 0 adjudicated pilot cases | `not_measured` |
| Repair turns and time to green | event ledgers captured | 12 event ledgers | `pending_review` |
| Rollback/reopen | not observed | 0 eligible merges | `not_observed` |
| UI behavior/visual defects | not observed | 0 routed UI pilot trials | `not_applicable` |
| Cost, tokens, latency, and intervention | traces captured; exact provider tokens unavailable | 12 pilot attempts | `pending_review` |

No workflow win/loss/tie conclusion is reported here. The protected mapping SHA
is `b4f525d1b7d928386f09e608d79f67ce369159c8029375e3bd2785fdcb5879e4`; it must
remain unavailable to the blind reviewer until all six pair reports are frozen.

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
| Results include wins and failures | pending | six blind pair packages prepared; human review not frozen |
| Final adoption decision recorded | not met | decision is not eligible and pending adjudication |
| Follow-up tasks created for gaps | met | TFA-7.2A through TFA-7.2C in `docs/tasks.md` |

TFA-7.2 is no longer blocked on execution approval or model runs. It remains
incomplete until blind reports are written, the protected mapping is joined by a
separate custodian/adjudicator, and a final adoption decision is recorded.

## Resume Conditions

Resume TFA-7.2 by giving only
`reports/test_first_pilot/shishki_bot_v1/review/shishki-tfa7-20260715/blind_review/`
to the blind reviewer. Do not provide the protected mapping or raw run root to
that reviewer. After six reports are frozen and digested, a separate custodian
may use the protected mapping for adjudication. Any missing review, mapping
access by the reviewer, version drift, invalid call, or unmet denominator remains
`inconclusive`; no extra call is permitted under the zero-retry budget.
