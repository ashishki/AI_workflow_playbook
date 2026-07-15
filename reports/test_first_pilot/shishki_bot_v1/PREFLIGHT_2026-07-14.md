# shishki_bot Pilot Preflight

Date: 2026-07-14
Status: static preparation passed; execution approval pending
Real-model/Codex executions: 0
Valid pilot pairs: 0
Empirical claims: none

## Repository Selection Checks

The GitHub connector identified Artem Shishkin's authenticated login as
`ashishki`. The selected public repository was
`https://github.com/ashishki/shishki_bot` at
`798bb0ed68f7dacdf7e6f697381b7a3222949d74`.

Clean temporary clones produced these local observations:

| Scope | Result |
|-------|--------|
| Current `main` | 99 pytest tests passed; Ruff check passed; Ruff format passed; integrity passed; skill gate passed with 0 skills |
| PR #2 base `59ff47b...` | 97 pytest tests passed; Ruff check passed; integrity passed |
| PR #3 base `5f9adb4...` | 98 pytest tests passed; Ruff check passed; integrity passed |

Tests used synthetic/in-memory project paths. No bot was started, no Telegram
token was supplied, and no production or client data was accessed. These are
repository-baseline observations, not pilot results.

## Fixture And Scorer Checks

- `harness-lab validate-suite` reports suite `shishki_bot_ci_v1`, version
  `1.0.0`, tasks 2.
- Both staged fixtures produce one expected RED failure before implementation.
- Replaying the two historical accepted files in disposable copies produces
  2 passing task-1 checks and 3 passing task-2 checks.
- A no-op command-adapter smoke produced two valid failed-task bundles; both
  bundle validators returned zero errors and warnings. These temporary bundles
  were deleted and are excluded from every pilot count.
- Focused preparation tests cover task-fact equality, sparse fixture paths and
  source hashes, RED states, counterbalanced 12-call scheduling, event schema,
  nested-session refusal, secret-environment removal, timeout process-group
  termination, trace bundling, append behavior, and scorer timeouts.

The durable static-preflight receipt is
`preflight_2026-07-14/receipt.json`; it records exit 0 and explicitly states that
no model invocation was attempted.

## Remaining Gates

The asset manifest, fresh Test Critic report, exact human approvals, and final
external execution decision are still required. The guarded runner cannot use
the active Codex session and cannot exceed 12 Codex executions or retry under the proposed
budget. A future CLI/config/suite digest change invalidates the pending scope.
