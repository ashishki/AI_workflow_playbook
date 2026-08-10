# Audited Execution And Feature Governance Plan

Date: 2026-08-10

## Baseline

- Branch: `master`
- HEAD: `51ea63571a737d94f460e3193e430a1045350613`
- Working tree before baseline: clean
- Baseline command environment: `.venv` is absent; `python3.12` exists but initially lacks `pytest` and `jsonschema`.
- Pre-existing baseline result: `python3.12 -m pytest -q` cannot start because `pytest` is missing. `tools/playbook_validate.py` and `tools/verify_playbook.py` fail primarily because `jsonschema`/`pytest` are missing in the environment. `git diff --check` passes.

## Current Feature Workflow State Machine

Current design lifecycle is:

`draft -> review_required -> approved -> implemented/superseded/rejected`

Current slice lifecycle is effectively:

`planned -> in_progress -> reviewed`, with legacy aliases such as
`implemented`, `closed`, `complete`, and `completed` treated as done by helper
sets.

The target slice lifecycle is:

`planned -> in_progress -> verification_failed -> review_required -> review_passed -> awaiting_human_acceptance -> accepted -> blocked/superseded`

Legacy reads will map `implemented -> review_required` and
`reviewed -> review_passed` with warnings. New writes must use only the target
states.

## Confirmed Bypass Paths

- Design approval can load required reviews only from
  `.playbook-artifacts/workflows/<feature-id>/required_reviews.json`; deleting
  that mutable projection makes required design reviews disappear.
- Design and slice review policy projections share one feature-level
  `required_reviews.json`, so slice review generation can overwrite design
  review status.
- Approval accepts review report refs but does not require machine-readable
  records bound to the exact current Feature Design markdown and canonical
  registry payload hashes.
- Planning `plan` writes a recommendation and may copy a declared
  `Planning-Depth` into `selected_planning_depth`; there is no explicit human
  selection artifact gate before `draft`.
- `next` opens dependent slices when dependencies are `reviewed`; it does not
  require deterministic acceptance evidence.
- `check` can mark a slice `reviewed` and return eligible status from current
  reports/checks; high-risk human acceptance is not a persisted external gate.
- Slice evidence is not fully hash-bound to candidate diff, post-state file
  manifest, verification receipts, review records, and accepted commit.
- `start` writes start state before context generation succeeds.
- `review --execute` exists as a CLI flag but has no implemented safe semantics.

## Authoritative Artifacts

- Feature Design markdown: `docs/design/<feature-id>.md`
- Feature Design registry: `docs/design/<feature-id>.design.json`
- Planning decision: `.playbook-artifacts/planning/<task-id>/planning_decision.json`
- Design review records:
  `.playbook-artifacts/reviews/<feature-id>/design/<role>.review.json`
- Design review projection:
  `.playbook-artifacts/workflows/<feature-id>/design/required_reviews.json`
- Slice review projection:
  `.playbook-artifacts/workflows/<feature-id>/slices/<slice-id>/required_reviews.json`
- Slice candidate result:
  `.playbook-artifacts/workflows/<feature-id>/slices/<slice-id>/candidate_result.json`
- Slice post-state manifest:
  `.playbook-artifacts/workflows/<feature-id>/slices/<slice-id>/post_state_manifest.json`
- Slice acceptance:
  `.playbook-artifacts/workflows/<feature-id>/slices/<slice-id>/acceptance.json`
- Audited run state:
  `.playbook-artifacts/audited-runs/<run-id>/manifest.json`,
  `audited_state.json`, and `result.json`

## State Model Changes

- Recompute required design review roles from `feature_review_policy.design_reviews(design)` at approval time.
- Treat `required_reviews.json` only as projection/cache/status report.
- Split design and slice review projections into phase-specific paths.
- Require dependency readiness from verified slice acceptance, not slice status text alone.
- Make high/critical risk green checks transition to
  `awaiting_human_acceptance`; low/medium can use policy auto-acceptance only
  when policy allows it and writes deterministic acceptance evidence.
- Revalidate accepted slice evidence on every dependency resolution so manual
  JSON edits cannot advance workflow.

## Evidence Model

- Review records bind role verdicts to report hash, current design markdown
  hash, current canonical registry payload hash, reviewer binding, and
  read-only provenance.
- Candidate result binds base commit, candidate commit, diff hash, post-state
  manifest hash, verification receipt hashes, maintainability report hash, and
  review record hashes.
- Acceptance binds accepted commit, candidate result hash, diff hash,
  verification hashes, review hashes, advisory acknowledgement, and human or
  policy acceptance method.
- Verification results distinguish `required` from optional checks; required
  failures block, optional failures create advisory evidence.

## Optional Audited Execution Architecture

Default execution profile remains `direct_codex`.

Experimental profile `audited_rounds` adds bounded round execution for one
accepted slice contract:

`accepted slice contract -> manager proposal -> fresh executor prompt/report -> read-only audit prompt/report -> deterministic apply-audit -> audited_state update`

The audited state stores verified requirements, verified facts, blockers,
receipt refs, open requirements, round counters, and budgets. It excludes raw
conversation history, hidden chain of thought, and unverified Executor prose as
operational truth.

The Feature Workflow remains the authority for what to build, boundaries,
roles, slice acceptance, and release readiness. Audited Execution is only an
optional mechanism for long slice execution and does not become a generic agent
runtime.

## Migration Strategy

- Read legacy slice statuses and old feature-level review projection paths.
- Write only new slice statuses and phase-specific review projections.
- Require new design review records for new approvals.
- Historical tasks without execution profile default to `direct_codex`.
- Initializer copies audited execution tools/schemas only for non-lean
  capability profiles; `lean-core` remains simple.

## Test Matrix

- Design approval: missing reports, deleted projection, stale design hash,
  missing marker, STOP_SHIP, advisory acknowledgement, fresh review records.
- Planning selection: needs input, no selection, accepted recommendation,
  override reason, stale decision after task/brief/planning facts edit.
- Slice state: start guards, high-risk acceptance gate, dependencies blocked
  until accepted, policy auto acceptance for allowed low/medium risk.
- Slice evidence: candidate/result/review/receipt/commit/dirty-tree freshness.
- Task binding: wrong task, wrong design ref, wrong slice id, planning-depth
  mismatch.
- Verification: required vs optional checks, legacy string warnings, no real
  required structured check.
- Audited execution: failed audit does not advance state, missing receipts
  blocked, verified audit advances state, done requires all requirements,
  budgets/no-progress stop, fresh context excludes old executor history.
- Security: absolute paths, `..`, symlink escape, auditor write attempts,
  executor audit-file writes, review records outside repo.

## Files

ADD:

- `schemas/audited_*.schema.json`
- `tools/audited_execution.py`
- `docs/audited_execution_protocol.md`
- `reports/implementation/AUDITED_EXECUTION_AND_FEATURE_GOVERNANCE_REPORT.md`
- audited-round fixtures under `companion/ai_workflow_harness_lab`

MODIFY:

- `tools/feature_workflow.py`
- `tools/approve_feature_design.py`
- `tools/feature_design_lib.py`
- `tools/feature_review_policy.py`
- `tools/playbook_validate.py`
- `tools/init_playbook_project.py`
- `schemas/feature_design.schema.json`
- existing Feature Workflow, initializer, and harness lab tests
- README/playbook/docs link surfaces

KEEP:

- Existing Feature Workflow actor roles and prompt renderer.
- Existing release resolver.
- Direct Codex workflow as the default path.
- LongHorizon-Harness as optional/deferred unless a stable interface is proven.

## Non-Goals

- No generic scheduler or autonomous multi-project runtime.
- No mandatory LongHorizon-Harness dependency.
- No model training, RL, distillation, teacher model calls, model-internal
  memory, ReOPD, Prime Intellect, or Molt integration.
- No claim that `audited_rounds` improves real-model quality before real Codex
  pilots produce empirical evidence.
