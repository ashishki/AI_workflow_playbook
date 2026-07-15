# shishki_bot Pilot Preflight

Date: 2026-07-15
Status: static preparation passed; execution approval pending
Real-model/Codex executions: 0
Valid pilot pairs: 0
Empirical claims: none

## Frozen Scope

The current frozen asset manifest contains 119 file digests.

- `ASSET_MANIFEST.sha256` SHA-256:
  `38e7e7742238db7e3ec3ef486a3f57ed12f94a425df90ad9dd581cbade8bf7d3`
- Static preflight receipt:
  `preflight_2026-07-15/receipt.json`
- Receipt SHA-256:
  `36d6410beb9638e1c67cd50f0a5e1bb99e7a058aeeb13987753d5f0df73075ad`
- stdout SHA-256:
  `ead50ec1462f0231cf6c70075d7c5b9cbf24e7a6d31a35654674ab141206bcc8`
- stderr SHA-256:
  `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`

## Static Checks

`tools/run_test_first_pilot.sh --preflight-only` exited 0 under
`tools/receipt_run.py`.

Observed terminal facts from the preflight stdout:

- frozen asset manifest verified: `asset manifest: ok (119 files)`
- suite validation reported `shishki_bot_ci_v1`, version `1.0.0`, tasks 2
- runner unit gate reported `77 passed`
- permission profile check reported workspace-only write, bounded read, and
  network denied
- final line: `pilot static preflight: ok; no model invocation attempted`

This preflight did not launch Codex model executions and does not count as pilot
evidence.

## Remaining Gates

TFA-7.1, TFA-7.2A, TFA-7.2B, and TFA-7.2C still require exact human approval
citing this manifest digest and critic record. The fresh critic record now exists at
`CRITIC_REVIEW.md` with SHA-256
`915c38d68bad83d332c4d5759ca4cd872c39e6aaa096c599ea6363214dfb0b42` and
terminal `Decision: ALLOW`. TFA-7.2 remains blocked until a named human launches
`tools/run_test_first_pilot.sh` from an external shell with a durable approval
record. Any manifest, critic, CLI, toolchain, prompt, suite, or approval change
invalidates this frozen candidate and requires a new preflight record.
