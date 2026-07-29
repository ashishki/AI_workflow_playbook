# Project Tasks

Status: active
Mode: {{MODE}}
Default-Planning-Depth: oneshot
Last updated: {{DATE}}

This task file is the project-level execution queue. Keep tasks small enough
that each one has clear acceptance criteria, verification commands, and review
evidence.

## Phase 1 - Bootstrap And Verification

### T01: Complete Project Brief And Mode Selection

Owner: human
Phase: 1
Type: governance
Status: planned
Risk-Level: low
Planning-Depth: oneshot
Public-Tests-Required: not_required
Critic-Required: not_required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Fill `docs/PROJECT_BRIEF.md`, choose Lean-Core / Standard / Strict mode,
  choose Planning Depth, and record why both choices are proportional to the
  project's risk and scope.

Acceptance-Criteria:
  - `docs/PROJECT_BRIEF.md` names the problem, operator, proof metric, current
    workaround, AI/model cost exposure, and external skill exposure.
  - The selected mode is recorded in this file and in the handoff prompt.
  - The selected Planning Depth is recorded as `oneshot`, `compact_design`, or
    `designed_slices`; any override from the deterministic recommendation has a
    human-readable reason.
  - Any omitted heavy artifact is explicitly marked optional or not applicable.

Verification:
  - manual review of `docs/PROJECT_BRIEF.md`

### T02: Establish Verification Baseline

Owner: codex
Phase: 1
Type: test
Status: planned
Risk-Level: low
Planning-Depth: oneshot
Public-Tests-Required: conditional
Critic-Required: not_required
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Add or confirm the project's first deterministic verification command before
  implementation work begins.

Acceptance-Criteria:
  - A local command or CI job exists for the current stack.
  - The baseline result is recorded in `docs/CODEX_PROMPT.md` or `AGENTS.md`.
  - Future tasks reference concrete verification commands.

Verification:
  - `{{VERIFY_COMMAND}}`

### T03: Configure Optional Cost And Skill Gates

Owner: codex
Phase: 1
Type: cost:telemetry, skill:security
Status: planned
Risk-Level: medium
Planning-Depth: oneshot
Public-Tests-Required: conditional
Critic-Required: conditional
Holdout-Required: not_required
Mutation-Required: not_required
Property-Required: not_required
Visual-Contract: not_applicable

Objective: |
  Enable cost telemetry and external-skill security gates only when the project
  actually uses LLM provider calls, agent loops, external skills, or dynamic
  routing/cascades.

Acceptance-Criteria:
  - `docs/COST_BUDGET.md` exists when AI/model usage is recurring or material.
  - `docs/ai_cost_architecture.md` exists when cost architecture is required.
  - `docs/router_eval.md` exists before dynamic routing or cascades.
  - `docs/security/skills/{skill-name}/TRUST_RECORD.md` exists before any
    third-party/cross-project skill is installed or enabled.

Verification:
  - `python3 tools/integrity_check.py --root .`
  - `python3 tools/skill_security_gate.py --root . --discover-agent-skills --require-scanner`

## Planning Fields

Use these fields only when the task risk justifies them. Tasks without
`Planning-Depth` are interpreted as legacy `oneshot` tasks.

- `Planning-Depth` values: `oneshot`, `compact_design`, `designed_slices`.
- `Design-Refs` example: `docs/design/F01.design.json`.
- `Slice-ID` example: `S01`.
- `User-Touchpoint` example: `User can complete the smallest observable workflow.`
- `Review-Checkpoint` example: `slice_review`, `closed`, or
  `docs/verification/T01_slice_review.md`.
- `Change-Budget` example: `files<=4, lines<=200`.
- `Maintainability-Risk` values: `low`, `medium`, `high`, `critical`.

`compact_design` requires an approved feature design before implementation.
`designed_slices` also requires a valid `Slice-ID`, user touchpoint, review
checkpoint, change budget, and satisfied slice dependencies.
