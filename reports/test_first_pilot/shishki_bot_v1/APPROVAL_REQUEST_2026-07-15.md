# Test-First Pilot Approval Request

Status: pending human approval
Request date: 2026-07-15
Scope: `shishki_bot_ci_v1/1.0.0`

This file is not a durable approval record. It exists to make the exact approval
scope reviewable before a human signs a separate record. The runner will reject
this file because its final non-empty line is not `Decision: approved`.

## Frozen Scope

- Repository: `ashishki/shishki_bot`
- Pilot registry: `reports/test_first_pilot/shishki_bot_v1/PILOT_REGISTRY.md`
- Static preflight: `reports/test_first_pilot/shishki_bot_v1/PREFLIGHT_2026-07-15.md`
- Frozen asset manifest SHA-256:
  `38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3`
- Fresh critic report SHA-256:
  `915c38d68bad83d332c4d5759ca4cd872c39e6aaa096c599ea6363214dfb0b42`
- Fresh critic terminal decision: `Decision: ALLOW`
- Static preflight result: exit 0; `77 passed`; no model invocation attempted

## Human Decisions Requested

The named human owner must approve all of the following before the full runner
may execute:

- TFA-7.1 paired pilot plan for the frozen manifest above.
- TFA-7.2A repository/data scope, sparse fixtures, provenance, and retention.
- TFA-7.2B external execution boundary, provider/model parameters, zero paid API
  fallback, zero retries, and exactly 12 subscription-backed Codex executions.
- TFA-7.2C scorers, ledger, schedule, missing-value rules, and protected
  reviewer/custodian boundary.
- Final execution gate from a separate human shell, not from an active Codex
  session.

## Approval Record Body

Create a separate durable approval record with concrete lowercase path-safe
values for `Approval ID` and `Pilot ID`. The record must end with
`Decision: approved` as its final non-empty line.

```text
# Test-First Pilot Approval

Approval ID: <3-64 lowercase path-safe characters>
Pilot ID: <3-64 lowercase path-safe characters>
Manifest SHA-256: 38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3
Critic report SHA-256: 915c38d68bad83d332c4d5759ca4cd872c39e6aaa096c599ea6363214dfb0b42
Approver: Artem Shishkin
TFA-7.1: approved
TFA-7.2A: approved
TFA-7.2B: approved
TFA-7.2C: approved
Repository: `ashishki/shishki_bot`
Fixture bases: `59ff47bdbcfb32fb1f128fcf6ac37f6fa0bd8c26`; `5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d`
Sparse fixture boundary: approved
External permission profile and verifier sandbox: approved
Scorers, ledger, schedule, and missing-value rules: approved
Local evidence boundary: trusted single-writer host; no concurrent mutation; no independent attestation
Codex executions: 12
Internal inference calls: not bounded
Paid API budget: USD 0
Retries: 0
Retention: raw 90 days; sanitized 365 days
Decision: approved
```

## External Launch Shape

After approval, launch from a separate shell where `codex login status` reports
`Logged in using ChatGPT`. Do not launch from an active Codex session.

```bash
export TFA_PILOT_APPROVAL_RECORD=/absolute/path/to/the/durable/approval.md
export TFA_PILOT_APPROVAL_ID=<same approval id>
export TFA_PILOT_ID=<same pilot id>
tools/run_test_first_pilot.sh
```

Any manifest, critic, approval, CLI, toolchain, prompt, fixture, or runner drift
requires a new request and preflight before execution.
