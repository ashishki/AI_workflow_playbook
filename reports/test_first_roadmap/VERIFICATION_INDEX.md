# Test-First Roadmap Verification Index

Date: 2026-07-13
Environment: repository `.venv`
Authority: command evidence only; not human approval or empirical pilot evidence

The final receipt set is stored under
`reports/test_first_roadmap/verification_2026-07-13-final/`. Every receipt uses
`playbook.command_receipt.v1`, records the exact interpreter/command, exit code,
stdout/stderr digests, repository commit, and dirty worktree state.

| Check | Receipt | Expected result |
|-------|---------|-----------------|
| Canonical tasks | `tasks/receipt.json` | 0 errors, 0 warnings |
| Active placeholders | `placeholders/receipt.json` | 0 errors, 0 warnings |
| Integrity references | `integrity/receipt.json` | exit 0; two pre-existing cognition-path warnings |
| Task schema/parser unit tests | `schema-unit/receipt.json` | all tests pass |
| Receipt/evidence-validator unit tests | `evidence-unit/receipt.json` | all tests pass |
| Roadmap `--bundle` validator form | `bundle-alias/receipt.json` | valid fixture passes |
| Patch whitespace | `diff-check/receipt.json` | clean |
| Full repository verifier | `full-verifier/receipt.json` | 17/17 required checks pass |

An earlier immutable pre-repair receipt set remains in
`verification_2026-07-13/`; it is retained as audit history and is not the final
evidence reference.

TFA-7.2 project-specific commands and bundles are absent. Their absence is
recorded separately in `reports/test_first_pilot/PREFLIGHT_NOT_RUN.md` and must
not be inferred as a passing check.
