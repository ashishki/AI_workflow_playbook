# AI Workflow Playbook - Compact Session State

Version: 1.3
Date: 2026-06-08
Status: active-core-framework

## Current State

- Product role: canonical governance and verification framework for the
  portfolio.
- Active phase: EL-1, evidence layer.
- Current task source: `docs/tasks.md`.
- Latest completed tasks: `AWP-ZT-001`, `AWP-ZT-002`, `AWP-ZT-003`,
  `AWP-ZT-004`, `AWP-PI-008`.
- Working rule: protocols must remain artifact-first and runtime-optional.

## Active Inputs

- `README.md`
- `PLAYBOOK.md`
- `docs/PROJECT_PLAN.md`
- `docs/tasks.md`
- `docs/runtime_verification_protocol.md`
- `docs/filesystem_reality_principle.md`
- `docs/readme_first_knowledge_index.md`
- `prompts/ORCHESTRATOR.md`

## Next Task

No active next task selected for this session.

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
task_id: AWP-PI-008
operation: codex_exec_subagent_protocol
claimed_files:
  - docs/CODEX_PROMPT.md
  - docs/codex_exec_subagent_protocol.md
  - docs/tasks.md
  - docs/usage_guide.md
  - README.md
  - templates/AGENTS.md
  - templates/CODEX_PROMPT.md
  - prompts/PROMPT_FIX_FROM_REVIEW.md
  - prompts/PROMPT_DOC_SYNC_AFTER_TASK.md
  - prompts/audit/PROMPT_0_META.md
  - prompts/audit/PROMPT_1_ARCH.md
  - prompts/audit/PROMPT_2_CODE.md
  - prompts/audit/PROMPT_3_CONSOLIDATED.md
  - prompts/audit/PROMPT_PRIVACY_REVIEW.md
  - reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256
  - tools/init_playbook_project.py
  - tools/render_codex_exec_prompt.py
  - tests/unit/test_render_codex_exec_prompt.py
tests_run:
  - command: .venv/bin/python -m pytest tests/unit/test_render_codex_exec_prompt.py -q
    status: passed
  - command: .venv/bin/python -m pytest tests/integration/test_initializer.py -q
    status: passed
  - command: .venv/bin/python tools/playbook_validate.py --root . --check tasks --check placeholders --check readiness --check delivery --check references
    status: passed_with_warnings
    notes:
      - "Existing manifest warnings: missing generated/cognition/index.json and docs/context-packets/."
  - command: python3 -m py_compile tools/render_codex_exec_prompt.py tests/unit/test_render_codex_exec_prompt.py
    status: passed
  - command: .venv/bin/python tools/build_test_first_pilot_manifest.py --write
    status: passed
  - command: .venv/bin/python -m pytest tests/unit/test_test_first_pilot_assets.py::test_frozen_asset_manifest_matches_full_execution_closure -q
    status: passed
  - command: .venv/bin/python -m pytest -q -k 'not test_frozen_permission_profile_denies_sibling_auth_and_network_access and not test_frozen_toolchain_matches_current_pilot_environment'
    status: passed
    notes:
      - "135 passed, 2 deselected."
  - command: .venv/bin/python tools/verify_playbook.py --root .
    status: failed_known_environment_drift
    notes:
      - "18/19 checks passed; pytest step failed on frozen Codex pilot toolchain drift."
      - "Observed local Codex CLI is 0.145.0 while frozen pilot permission/toolchain checks expect the pinned 0.144.4 environment."
verification_status: scoped_passed_with_known_frozen_toolchain_drift
```
