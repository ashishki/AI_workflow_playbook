# Current Session State

Project: {{PROJECT_NAME}}
Version: 1.0
Date: {{DATE}}
Phase: 1
Mode: {{MODE}}
Planning-Depth: {{PLANNING_DEPTH}}

## Current State

Baseline: pending T02; no tests or live agent execution claimed.
Scaffold generated; project-specific decisions and workflow acceptance pending.
Readiness: `.playbook/readiness_state.json`.

## Next Task

T01: Complete Project Brief And Mode Selection (`docs/tasks.md`), then T02:
Establish Verification Baseline. Reconcile roles/review route with owner intent.
For designed features: `tools/feature_workflow.py` uses
`plan -> select-plan -> draft -> review -> approve`, then the slice lifecycle.
Generated planning depth and a draft design are not approval.

## Fix Queue

empty

## Open Findings

none reported; unresolved scaffold decisions are not passed.

## Continuity Pointers

- `AGENTS.md`, `docs/IMPLEMENTATION_CONTRACT.md`: working rules.
- `.playbook/delivery_execution_model.json`: roles, task-loop status, model bindings.
- `docs/REVIEW_POLICY.md`, `docs/merge_authority.md`: review and authority.
- `docs/PROJECT_BRIEF.md`, `docs/tasks.md`: outcome, task and Context-Refs.
- `docs/DECISION_LOG.md`, `docs/IMPLEMENTATION_JOURNAL.md`: decisions and history.
- `docs/EVIDENCE_INDEX.md`: check/review evidence; cognition manifest if present.

## Instructions for Codex

Read AGENTS, the current task and applicable contract rules before editing.
Run `python tools/verify_project.py --root .`; record command/result/evidence.
Current result: not run (pending T02). Use `docs/REVIEW_POLICY.md` for scoped
review dispatch and correction limits; load the exec protocol only when selected.
Keep this handoff short: replace current state, do not append completed history
or reusable prompts. Pass children a bounded task digest and required references.

## RAG State

Status: {{RAG_STATE}}
Resolve against `docs/ARCHITECTURE.md`; active details/evidence: `docs/retrieval_eval.md`.

## Tool-Use State

Status: {{TOOL_USE_STATE}}
Resolve against architecture; active details/evidence: `docs/tool_eval.md`.

## Agentic State

Status: {{AGENTIC_STATE}}
Resolve against architecture; active details/evidence: `docs/agent_eval.md`.

## Planning State

Status: {{PLANNING_STATE}}
Resolve against architecture; active details/evidence: `docs/plan_eval.md`.

## Compliance State

Status: {{COMPLIANCE_STATE}}
Resolve against architecture; active details/evidence: `docs/compliance_eval.md`.

## Evaluation State

Last Evaluation: not run; no evaluated task yet.
Eval Source: pending applicable task; record exact command and artifact.
Date: not run; record actual evaluation date with its task/diff.
Regression Thresholds: pending active evaluation contract; no baseline measured.

## NFR Baseline

Not measured. When `docs/nfr.md` exists, link current measurements and targets.
Profile pointers above are conditional, not proof that optional artifacts exist.
Before implementation, resolve each profile ON/OFF; OFF details are n/a. ON
profiles require current canonical artifacts/evidence, loaded only when relevant.
