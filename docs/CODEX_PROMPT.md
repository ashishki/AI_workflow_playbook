# AI Workflow Playbook - Compact Session State

Version: 1.2
Date: 2026-05-29
Status: active-core-framework

## Current State

- Product role: canonical governance and verification framework for the
  portfolio.
- Active phase: EL-1, evidence layer.
- Current task source: `docs/tasks.md`.
- Latest completed tasks: `AWP-ZT-001`, `AWP-ZT-002`, `AWP-ZT-003`.
- Working rule: protocols must remain artifact-first and runtime-optional.

## Active Inputs

- `README.md`
- `PLAYBOOK.md`
- `docs/PROJECT_PLAN.md`
- `docs/tasks.md`
- `docs/runtime_verification_protocol.md`
- `docs/filesystem_reality_principle.md`
- `prompts/ORCHESTRATOR.md`

## Next Task

`AWP-EL-001`: Playbook-Native Receipt Schemas.

## Fix Queue

empty

## Open Findings

none

## Runtime Verification

Runtime verification is required for risky prompt/template/protocol changes.
Use `templates/RUNTIME_VERIFICATION_RECORD.md` when the shortened form is not
enough.

Last verification:

```yaml
type: runtime_verification
task_id: AWP-ZT-001
operation: docs_template_and_review_update
claimed_files:
  - docs/CODEX_PROMPT.md
  - docs/bounded_correction_turns.md
  - docs/runtime_verification_protocol.md
  - docs/tasks.md
  - templates/RUNTIME_VERIFICATION_RECORD.md
  - templates/CODEX_PROMPT.md
  - templates/tasks_schema.md
  - prompts/audit/PROMPT_2_CODE.md
  - prompts/audit/PROMPT_3_CONSOLIDATED.md
tests_run:
  - command: git diff --check
    status: passed
  - command: python3 tools/integrity_check.py --root .
    status: passed_with_warnings
    notes:
      - "Existing manifest warnings: missing generated/cognition/index.json and docs/context-packets/."
  - command: python3 -m py_compile tools/integrity_check.py
    status: passed
verification_status: passed
```
