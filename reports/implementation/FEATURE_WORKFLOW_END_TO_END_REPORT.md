# Feature Workflow End-To-End Report

Date: 2026-07-29
Branch: master
Base commit: c980381d4df914a5f8544e45cab25270b33d5cec
Final HEAD: c980381d4df914a5f8544e45cab25270b33d5cec
Working tree: dirty with intentional implementation changes; no commit created

## Baseline

Starting state matched the expected Planning Depth baseline:

- `cfa4fde` planning depth design contracts
- `d21f5c8` design review markers and changeability harness
- `0f4dcc0` planning depth documentation
- `c980381` feature design template whitespace cleanup

No diff existed after `c980381` before this work.

Baseline commands:

- `python -m pytest -q`: failed because `python` is not on PATH.
- `python tools/verify_playbook.py --root .`: failed because `python` is not
  on PATH.
- `python tools/playbook_validate.py --root .`: failed because `python` is not
  on PATH.
- `git diff --check`: passed.

Repository interpreter baseline stayed consistent with the prior known drift:
pytest failed only on frozen Codex/toolchain checks.

## Actor Model

- Deterministic tools collect facts, recommend Planning Depth, validate schemas,
  check hashes, select slices, render bounded context, run verification receipts,
  check scope/budget, parse review markers, and write status/evidence.
- Main Codex can act as `design_author` during design phase. It may draft or
  revise Feature Design and task planning artifacts, but must not write
  application code or approve design.
- Main Codex can later act as slice implementer only after fresh human approval.
  It receives current-slice context and must not approve completion.
- Isolated Codex reviewers use read-only `codex exec` prompts for
  `product_design_review`, `program_design_review`, `slice_review`, and
  `maintainability_review`.
- Human authority remains required for Planning Depth overrides, exact design
  approval, advisory acceptance, high-risk slice acceptance, and final
  completion/release decisions.

## Implemented Flow

Implemented `tools/feature_workflow.py` as the single thin coordinator:

- `plan`: writes deterministic Planning Facts and recommendation to
  `.playbook-artifacts/planning/<task-id>/planning_decision.{json,md}`.
- `draft`: creates/uses Feature Design scaffold, records design-only session
  boundary, and writes `.playbook-artifacts/prompts/<feature-id>/design_author.md`.
- `review`: resolves required design or slice review roles, writes prompts and
  suggested read-only `codex exec` commands, parses markers when reports exist,
  and writes `required_reviews.json`.
- `approve`: delegates to interactive human-only approval CLI.
- `status`: writes and prints workflow status without creating release
  readiness.
- `next`: selects the first planned slice whose dependencies are reviewed and
  whose design approval is fresh.
- `start`: records slice base commit/dirty state, changes only slice operational
  status to `in_progress`, and renders context.
- `context`: wraps the bounded slice context with planning decision refs,
  approval hashes, structured verification, and explicit implementation-only
  instructions.
- `check`: compares diff against the recorded base commit, checks
  allowed/forbidden files and budget, runs structured verification through
  `receipt_run.py`, runs maintainability signals, creates review prompts, parses
  reports, writes `slice_result.json`, and marks a slice `reviewed` only when
  deterministic checks and required reviews pass.

## Files

Added:

- `tools/approve_feature_design.py`
- `tools/feature_review_policy.py`
- `tools/feature_workflow.py`
- `tests/unit/test_feature_workflow.py`
- `reports/design/feature_workflow_completion_plan.md`
- `reports/implementation/FEATURE_WORKFLOW_END_TO_END_REPORT.md`

Modified:

- `tools/feature_design_lib.py`
- `tools/render_codex_exec_prompt.py`
- `tools/render_slice_context.py`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `schemas/feature_design.schema.json`
- `templates/FEATURE_DESIGN.md`
- `README.md`, `PLAYBOOK.md`, usage/adoption/protocol/tool docs
- tests and frozen asset manifest

Intentionally unchanged:

- Existing release readiness resolver.
- Existing Playbook Mode semantics.
- Existing synthetic changeability mechanism implementation.
- Existing historical task IDs.

## Approval Integrity

Canonical registry payload hash algorithm:

1. Start from the companion JSON registry.
2. Remove top-level `status`.
3. Remove approval fields:
   `approved_by`, `approved_at`, `approval_method`, `approval_ref`,
   `approval_notes`, `advisory_acknowledgement`,
   `approved_markdown_sha256`, `approved_registry_payload_sha256`,
   `approved_review_refs`.
4. Remove each slice's operational `status`.
5. Serialize JSON with sorted keys and compact separators.
6. Compute SHA-256 of the UTF-8 bytes.

Approval is fresh only when:

- status is `approved` or `implemented`;
- human/authorized provenance is valid;
- model/Codex self-approval is absent;
- Markdown hash matches;
- canonical registry payload hash matches;
- approved review report hashes still match;
- approved review verdicts are `PASS` or acknowledged `ADVISORY`.

Approval becomes stale when design Markdown, planning depth, risk, refs, slice
set, slice outcome/scope, allowed/forbidden files, interfaces, verification,
dependencies, change budget, or rollback changes. Approval stays fresh when
only slice operational status changes or `.playbook-artifacts` execution
evidence is added.

Production approval requires an interactive TTY. Unit/integration tests use
internal approval functions with `approval_method=test_harness`; there is no
production flag that lets Codex bypass human approval.

## Tests

Focused regression:

- `.venv/bin/python -m pytest tests/unit/test_feature_design.py tests/unit/test_feature_workflow.py tests/unit/test_slice_context.py tests/unit/test_maintainability_check.py tests/unit/test_render_codex_exec_prompt.py tests/unit/test_playbook_validate.py tests/integration/test_initializer.py companion/ai_workflow_harness_lab/tests/test_cli.py -q`
- Result: 101 passed.

Post-filter focused regression:

- `.venv/bin/python -m pytest tests/unit/test_feature_workflow.py tests/unit/test_feature_design.py tests/unit/test_render_codex_exec_prompt.py tests/integration/test_initializer.py -q`
- Result: 45 passed.

Full pytest:

- `.venv/bin/python -m pytest -q`
- Result: 206 passed, 2 failed.
- Failures are the pre-existing frozen pilot drift:
  `test_frozen_permission_profile_denies_sibling_auth_and_network_access` and
  `test_frozen_toolchain_matches_current_pilot_environment`.

Validators and smoke:

- `.venv/bin/python tools/playbook_validate.py --root . --check schemas --check tasks --check design --check instructions --check references`: errors=0, warnings=2.
- `.venv/bin/python tools/validate_feature_design.py --root .`: errors=0, warnings=0.
- `PYTHONPATH=companion/ai_workflow_harness_lab/src .venv/bin/python -m ai_workflow_harness_lab.cli changeability-run --suite companion/ai_workflow_harness_lab/suites/changeability_synthetic_v1/suite.json --output .playbook-artifacts/changeability-smoke-2`: passed; mechanism demonstration only.
- End-to-end feature workflow fixture passed:
  `{"approval": "test_harness", "design_reviews": "pass", "draft": 0, "next": "F01-S2", "plan": 0, "scenario": "feature_workflow_e2e", "slice_review": "pass"}`.
- `git diff --check`: passed.

Full verifier:

- `.venv/bin/python tools/verify_playbook.py --root .`
- Result: `required_failures=1`, because the required pytest step has the same
  two frozen Codex/toolchain failures.
- All other verifier steps passed.

## Remaining Limits

- Independent reviewer isolation uses a separate Codex process/thread but the
  same model family by default.
- Human identity is procedural, not cryptographically attested.
- Design quality still requires judgment; deterministic tools validate
  boundaries and evidence, not architectural taste.
- Changeability synthetic fixture is not empirical maintainability evidence.
- No autonomous multi-project orchestration is claimed.
- `feature_workflow.py` is a thin script entrypoint, not the final installable
  unified `playbook` CLI.

## Next Steps

1. Build the unified installable `playbook feature ...` and `playbook slice ...`
   CLI wrapper.
2. Implement the real sequential changeability runner for Task A -> state A ->
   Task B -> state B -> Task C.
3. Add semantic context-budget audit for near-duplicate/conflicting
   instructions.
4. Add optional second-model reviewer support without making it completion
   authority.
5. Integrate ProofLoop later, after this workflow is stable and measured.
