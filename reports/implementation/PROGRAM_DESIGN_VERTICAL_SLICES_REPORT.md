# Program Design And Vertical Slices Implementation Report

Date: 2026-07-29
Base commit: 5583eca96c4d2d480b5574ed78bea63e0b07ebf0
Final HEAD: 5583eca96c4d2d480b5574ed78bea63e0b07ebf0
Working tree: dirty with intentional implementation changes; no commit created

## Summary

Implemented Planning Depth as an orthogonal dimension to Playbook Mode:

- `oneshot`
- `compact_design`
- `designed_slices`

Added Feature Design Markdown plus companion JSON registry, readiness gates,
vertical slice validation, slice context packets, design/slice/maintainability
review roles, retrofit scaffolding, and a synthetic changeability sequence
mechanism.

The implementation does not add a runtime, hosted service, database, web UI,
paid model call, or required multi-agent orchestration.

## Primary Files

- `templates/FEATURE_DESIGN.md`
- `schemas/feature_design.schema.json`
- `schemas/instruction_manifest.schema.json`
- `schemas/changeability_suite.schema.json`
- `schemas/changeability_result.schema.json`
- `tools/planning_depth.py`
- `tools/feature_design_lib.py`
- `tools/create_feature_design.py`
- `tools/validate_feature_design.py`
- `tools/render_slice_context.py`
- `tools/check_maintainability.py`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `tools/render_codex_exec_prompt.py`
- `companion/ai_workflow_harness_lab/src/ai_workflow_harness_lab/changeability.py`
- `companion/ai_workflow_harness_lab/suites/changeability_synthetic_v1/suite.json`
- `docs/adr/ADR-002-feature-design-companion-json.md`

## Contracts

- Task schema remains `playbook.task.v1`; new fields are optional and legacy
  tasks default to `planning_depth=oneshot` and
  `planning_depth_source=legacy_default`.
- Feature Design registry schema is `playbook.feature_design.v1`.
- Instruction manifest schema is `playbook.instruction_manifest.v1`.
- Readiness state remains `playbook.readiness_state.v1` and now supports
  `brief_ready` and `design_required` while preserving compatibility states.
- Changeability schemas are mechanism-only:
  `playbook.changeability_suite.v1` and `playbook.changeability_result.v1`.

## Verification Commands

Exact requested commands:

- `python -m pytest -q`: failed, `/bin/bash: python: command not found`
- `python tools/verify_playbook.py --root .`: failed, `/bin/bash: python: command not found`
- `python tools/playbook_validate.py --root .`: failed, `/bin/bash: python: command not found`
- `git diff --check`: passed

Repository interpreter commands:

- `.venv/bin/python -m pytest -q`: 191 passed, 2 failed
- `.venv/bin/python tools/verify_playbook.py --root .`: required_failures=1
  because pytest has the same two frozen toolchain failures
- `.venv/bin/python tools/playbook_validate.py --root .`: errors=0,
  warnings=2
- `.venv/bin/python tools/playbook_validate.py --root . --check schemas --check tasks --check design --check instructions --check references`: errors=0, warnings=2
- `.venv/bin/python tools/validate_feature_design.py --root .`: errors=0,
  warnings=0
- `PYTHONPATH=companion/ai_workflow_harness_lab/src .venv/bin/python -m ai_workflow_harness_lab.cli changeability-run --suite companion/ai_workflow_harness_lab/suites/changeability_synthetic_v1/suite.json --output .playbook-artifacts/changeability-smoke`: passed

Focused regression suites:

- Planning/design/readiness/initializer/slice/review/maintainability/Harness CLI
  focused set: 87 passed
- Slice 3 focused set: 55 passed
- Slice 4 focused set: 22 passed
- Harness Lab CLI focused set: 24 passed

## Known Failures

Pre-existing environment/toolchain drift remains:

- `tests/unit/test_test_first_pilot_permissions.py::test_frozen_permission_profile_denies_sibling_auth_and_network_access`
  fails because the current Codex CLI does not match the frozen pilot.
- `tests/unit/test_test_first_pilot_toolchain.py::test_frozen_toolchain_matches_current_pilot_environment`
  fails because the host platform/Codex CLI digests differ from the frozen
  pilot lock.

During implementation, the frozen asset manifest became stale because the
Playbook execution closure changed. It was updated with:

`./.venv/bin/python tools/build_test_first_pilot_manifest.py --write`

The asset manifest check then passed.

Existing reference warnings remain:

- `docs/COGNITION_MANIFEST.md` references `generated/cognition/index.json`
- `docs/COGNITION_MANIFEST.md` references `docs/context-packets`

## Scenario Evidence

Scenario A, new project:

`{"context": 0, "init": 0, "next_slice": "S02", "release": 0, "scenario": "A", "validate": 0, "verify": 0}`

Covered strict initialization with `designed_slices`, draft design-required
state, human-approved design registry, implementation readiness after scaffold
markers were resolved, Slice S01 context packet, project verifier, next slice
S02, and release resolver.

Scenario B, retrofit:

`{"app_preserved": true, "init": 0, "planning_depth": "designed_slices", "scenario": "B", "state": "design_required", "validate": 0}`

Covered existing `AGENTS.md` and application file preservation, repository
inventory, retrofit plan, recommended planning depth, design scaffold, and
validator next-state behavior without application code generation.

## Deferred Work

- Unified `playbook design ...` and `playbook slice ...` CLI wrapper. Current
  implementation provides thin scripts and documents future mapping.
- Semantic near-duplicate/conflict detection for instruction manifests.
- Production-grade longitudinal changeability benchmark. Current suite is a
  synthetic mechanism demonstration only.
- Automatic protected holdout or human approval storage. Approval remains an
  explicit human-authored registry update.

## Maturity Claims

Supported:

- Deterministic planning-depth recommendation rules.
- Deterministic validation of design approval, path safety, and slice registry.
- Draft design blocks implementation readiness when design is required.
- Read-only design/slice/maintainability review prompt roles with fail-closed
  markers.
- Retrofit scaffolding preserves existing files by default.

Not claimed:

- No empirical proof that Planning Depth improves maintainability in real
  repositories.
- No automatic architecture approval.
- No automatic release readiness.
- No mandatory multi-agent orchestration.

## Migration Notes

- Historical tasks without `Planning-Depth` remain valid as legacy `oneshot`
  tasks.
- New strict requirements apply when a task or readiness state explicitly adopts
  `compact_design` or `designed_slices`.
- Existing generated projects should copy `tools/feature_design_lib.py` if they
  update to the new `tools/playbook_validate.py`, because the validator imports
  the shared Feature Design helper.
- `compact_design` and `designed_slices` designs require companion JSON approval
  provenance; `approved_by=codex` is invalid.
