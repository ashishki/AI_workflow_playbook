# Feature Workflow Completion Plan

Date: 2026-07-29
Base commit: c980381d4df914a5f8544e45cab25270b33d5cec
Branch: master

## Already Implemented

- Planning Depth is defined independently from Playbook Mode:
  `oneshot`, `compact_design`, `designed_slices`.
- Feature Design has a Markdown template and companion JSON registry.
- Task parsing accepts planning/design/slice fields with legacy
  `oneshot` defaults.
- Feature Design registry validation checks schema, path safety, approval
  provenance, slices, dependencies, and change budgets.
- Slice context rendering creates bounded packets from the brief, approved
  design, current slice, architecture refs, and instruction manifest.
- Codex exec prompts support design/slice/maintainability review roles with
  deterministic markers.
- Maintainability checks emit advisory and stop-ship signals without an
  aggregate score.
- Harness Lab has a synthetic changeability sequence mechanism.

## Confirmed Gaps

- Planning inputs are not yet captured as deterministic artifacts.
- Feature Design authoring lacks one canonical prompt/workflow entrypoint.
- Design author, implementer, reviewer, and human authority are documented but
  not enforced by workflow artifacts.
- Design approval is not bound to exact Markdown/registry hashes and can become
  stale silently.
- Design-only work can drift into application code before approval.
- Review roles are available but not selected by a deterministic policy
  resolver.
- Slice lifecycle is not yet automated across next/start/context/check.
- Structured slice verification is not executable through receipts.

## Authoritative Artifacts

- Planning policy: `tools/planning_depth.py`
- Feature Design registry: `schemas/feature_design.schema.json`
- Feature Design template: `templates/FEATURE_DESIGN.md`
- Shared design validation: `tools/feature_design_lib.py`
- Task contract: `schemas/task.schema.json` and `tools/playbook_validate.py`
- Review prompt/marker contract: `tools/render_codex_exec_prompt.py` and
  `docs/codex_exec_subagent_protocol.md`
- Context loading policy: `schemas/instruction_manifest.schema.json` and
  `tools/render_slice_context.py`
- Command evidence: `tools/receipt_run.py`

## New Files Needed

- `tools/feature_workflow.py` as the thin coordinator entrypoint.
- `tools/approve_feature_design.py` for interactive human-only approval.
- `tools/feature_review_policy.py` for deterministic review requirements.
- `tests/unit/test_feature_workflow.py` for end-to-end workflow semantics.
- `reports/implementation/FEATURE_WORKFLOW_END_TO_END_REPORT.md` for final
  evidence.

## Existing Files To Extend

- `tools/feature_design_lib.py`
- `tools/render_codex_exec_prompt.py`
- `tools/render_slice_context.py`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `schemas/feature_design.schema.json`
- `templates/FEATURE_DESIGN.md`
- Documentation: `README.md`, `PLAYBOOK.md`, `docs/usage_guide.md`,
  `docs/adoption_modes.md`, `docs/codex_exec_subagent_protocol.md`,
  `tools/README.md`, `templates/AGENTS.md`, `templates/CODEX_PROMPT.md`
- Harness docs only; no production-grade changeability runner in this slice.

## Manual And Human-Controlled Boundaries

- Human approval remains interactive and cannot be provided by Codex.
- Planning Depth overrides require a recorded human reason.
- Advisory review findings are shown to the human and require recorded
  acknowledgment before approval.
- Isolated reviewer reports are evidence, not completion authority.
- Final completion and release readiness remain outside this workflow and are
  handled by existing human/release resolver authority.

## Vertical Implementation Slices

1. Approval integrity:
   add canonical hashes, stale detection, structured verification schema, and
   approval tests.
2. Workflow coordinator foundation:
   add `feature_workflow.py` plan/draft/status/next/start/context/check and
   design-only session boundary.
3. Review policy:
   add deterministic required review resolver, prompt generation, marker
   parsing, report hashes, and approval binding.
4. Slice execution:
   run structured verification through receipts, enforce allowed/forbidden
   files and budgets, and write `slice_result.json`.
5. Initializer/docs/report:
   point generated projects at the coordinator, document the actor model, keep
   Harness Lab claims synthetic, and record final verification.
