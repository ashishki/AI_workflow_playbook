# Reports Archive Index

Status: evidence archive index, not authority
Last updated: 2026-08-15

The `reports/` tree stores committed evidence, implementation reports, smoke
outputs, and historical pilot artifacts. Do not load `reports/**` by default
when starting ordinary Playbook work. Start with `docs/EVIDENCE_INDEX.md`, this
index, or the current task's explicit evidence references.

## Current Audit And Implementation Evidence

- `audit/MINIMALITY_AUDIT_2026-08-15.md` - read-only structural audit and the
  ordered cleanup backlog for reducing code, tests, generated artifacts, and
  default context without weakening assurance gates.
- `implementation/AUDITED_EXECUTION_AND_FEATURE_GOVERNANCE_REPORT.md` - current
  report for Feature Workflow governance hardening and the experimental
  audited-round mechanism.
- `implementation/FEATURE_WORKFLOW_END_TO_END_REPORT.md` - implementation report
  for the Planning Depth / Feature Design / Vertical Slice workflow.
- `implementation/PROGRAM_DESIGN_VERTICAL_SLICES_REPORT.md` - implementation
  report for the initial design-contract slice.
- `design/audited_execution_and_feature_governance_plan.md` - pre-implementation
  plan for audited execution and Feature Workflow governance hardening.
- `design/feature_workflow_completion_plan.md` - pre-implementation plan for
  the feature workflow lifecycle.
- `design/program_design_vertical_slices_plan.md` - pre-implementation plan for
  Planning Depth and Feature Design contracts.

## Historical Implementation Evidence

- `implementation/FINAL_IMPLEMENTATION_REPORT.md` - historical implementation
  report from the July 2026 test-first workstream.
- `receipts/final-*` - historical final verification receipts. Use only when
  cited by a current evidence index or task.

## Evaluation And Pilot Archives

- `playbook_eval/` - historical companion harness baseline-vs-Playbook
  demonstration output. It validates mechanism, not product improvement.
- `test_first_pilot/` - first paired pilot archive. The adjudicated result did
  not support a quality/productivity improvement claim.
- `test_first_roadmap/` - historical scope and verification records for the
  test-first roadmap workstream.
- `rag_eval/` - RAG Evaluation v2 smoke outputs. Current RAG contracts live in
  `docs/rag/`, `schemas/rag_eval_*.schema.json`, and `tools/rag_eval_*.py`.

## Generated Runtime Evidence

New runtime outputs should usually go under `.playbook-artifacts/`, which is
ignored by git. Commit a report under `reports/` only when it is durable
evidence for a task, ADR, release decision, or empirical claim.
