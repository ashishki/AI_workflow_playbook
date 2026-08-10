# Audited Execution And Feature Governance Report

Date: 2026-08-10

## Baseline

- Branch: `master`
- Base commit: `51ea63571a737d94f460e3193e430a1045350613`
- Initial working tree: clean
- Initial `.venv`: absent
- Environment setup: created ignored local `.venv`, installed
  `requirements-dev.txt`, and installed companion lab editable for real tests.

Existing failures after environment setup:

- Full pytest: `201 passed, 3 skipped, 4 failed`
- Failures were frozen pilot/toolchain environment failures:
  Codex CLI version mismatch and missing `/usr/bin/bwrap`.
- `playbook_validate`: 6 missing historical frozen pilot refs in
  `docs/tasks.md`, plus 2 cognition warnings.
- `verify_playbook`: required failures in `playbook_validate` and `pytest`.

## Feature Workflow Fixes

Authoritative review policy:

- Design approval now recomputes required roles from
  `feature_review_policy.design_reviews(design)`.
- `.playbook-artifacts/workflows/<feature-id>/design/required_reviews.json`
  is only a projection.
- Required design review records live at
  `.playbook-artifacts/reviews/<feature-id>/design/<role>.review.json`.
- Approval rejects missing records, stale design hashes, stale report hashes,
  missing markers, `STOP_SHIP`, and unacknowledged `ADVISORY`.

Planning selection:

- Added `feature_workflow select-plan --task <id>`.
- `plan` records recommendation and planning input hashes; it does not
  silently select the recommendation.
- `draft/review/start/context/check/accept-slice` require a selected, fresh
  planning decision and consistent task/design/slice binding.

State machine:

- New slice lifecycle writes:
  `planned`, `in_progress`, `verification_failed`, `review_required`,
  `review_passed`, `awaiting_human_acceptance`, `accepted`, `blocked`,
  `superseded`.
- Legacy `implemented` and `reviewed` are read as aliases with warnings.
- Only fresh `accepted` evidence satisfies slice dependencies.

Slice acceptance:

- `check` writes hash-bound `candidate_result.json` and post-state manifest.
- Low/medium risk can policy-auto accept only when no advisory is present.
- High/critical risk moves to `awaiting_human_acceptance`.
- Added interactive `accept-slice`, with pure resolver used by tests.
- Acceptance requires clean tree, committed candidate diff, current manifests,
  unchanged receipts/reviews, and human provenance.

Evidence freshness:

- Dependency resolution revalidates acceptance file, candidate result hash,
  post-state manifest hash, accepted commit ancestry, and file hashes.
- Manual status edits do not open dependent slices without acceptance evidence.

## Audited Execution

Roles:

- Manager proposes bounded rounds.
- Executor report is always `trust_status=unverified`.
- Auditor is read-only and produces evidence/findings only.
- Deterministic `apply-audit` updates audited state.

Round lifecycle:

`init -> next -> executor-prompt -> audit-prompt -> apply-audit -> status/stop`

State trust model:

- Audited state stores verified requirements, verified facts, blockers, open
  requirements, audit refs, counters, and budgets.
- It excludes raw Executor history and hidden chain of thought.

Budgets:

- Manifest stores max rounds, wall clock, repeated failure count, no-progress
  rounds, tool-call budget, cost ceiling/unknown, and human escalation policy.

Adapter boundary:

- LongHorizon-Harness is not a required dependency.
- Official repo/paper were reviewed. The current implementation keeps an
  export/import pilot boundary and does not invent a fake stable adapter.

## Files

ADD:

- `docs/audited_execution_protocol.md`
- `reports/design/audited_execution_and_feature_governance_plan.md`
- `reports/implementation/AUDITED_EXECUTION_AND_FEATURE_GOVERNANCE_REPORT.md`
- `schemas/audited_*.schema.json`
- `companion/.../audited_execution.py`
- `companion/.../tests/test_audited_execution.py`
- `companion/.../suites/audited_rounds_demo_v1/`

MODIFY:

- `tools/feature_workflow.py`
- `tools/approve_feature_design.py`
- `tools/feature_design_lib.py`
- `tools/feature_review_policy.py`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `schemas/feature_design.schema.json`
- Feature Workflow, validator, prompt, slice context, initializer, and
  companion tests
- README/PLAYBOOK/docs/templates/tool docs
- `reports/test_first_pilot/shishki_bot_v1/ASSET_MANIFEST.sha256`

KEEP:

- Existing release resolver
- Default `direct_codex`
- Human approval authority
- LongHorizon-Harness optional/deferred

Deferred:

- Real LongHorizon adapter with pinned upstream version/commit
- Real paired Codex pilot
- Cryptographic attestation

## Tests

Commands run:

- `.venv/bin/python -m pytest tests/unit/test_feature_design.py tests/unit/test_feature_workflow.py companion/ai_workflow_harness_lab/tests/test_audited_execution.py companion/ai_workflow_harness_lab/tests/test_cli.py::test_audited_run_cli_init_and_status tests/integration/test_initializer.py -q`
  - Result: `58 passed`
- `.venv/bin/python -m pytest tests/unit/test_maintainability_check.py tests/unit/test_playbook_validate.py tests/unit/test_render_codex_exec_prompt.py tests/unit/test_slice_context.py -q`
  - Result: `38 passed`
- `.venv/bin/python -m pytest -q`
  - Result: `220 passed, 3 skipped, 4 failed`
  - Remaining failures: frozen pilot/toolchain environment only.
- `.venv/bin/python tools/playbook_validate.py --root .`
  - Result: 6 historical missing frozen pilot refs, 2 cognition warnings.
- `.venv/bin/python tools/verify_playbook.py --root .`
  - Result: `required_failures=2` (`playbook_validate`, `pytest`).
- `git diff --check`
  - Result: pass.

Artifacts:

- `.playbook-artifacts/playbook_verification.json`
- `.playbook-artifacts/audited-runs/...` in tests
- `.playbook-artifacts/workflows/<feature>/slices/<slice>/candidate_result.json`
  in tests

Frozen pilot note:

- `ASSET_MANIFEST.sha256` was regenerated because this implementation
  intentionally changed files inside its declared closure (`tools`, `tests`,
  `schemas`, and companion lab). This is a closure migration, not a behavioral
  fixture update to hide a failure.

## Maturity

- Feature Workflow governance: tested.
- Audited execution mechanism: tested.
- External LongHorizon adapter: deferred behind export/import boundary.
- Real-model benefit: not yet established.

Remaining limits:

- Same model family may still be used for roles.
- Human identity is procedural.
- No cryptographic attestation.
- No empirical quality claim.
- No autonomous multi-project runtime.
- No ReOPD or model training.
