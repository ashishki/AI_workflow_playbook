# Project Tasks

Status: active
Mode: {{MODE}}
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

Objective: |
  Fill `docs/PROJECT_BRIEF.md`, choose Lean / Standard / Strict mode, and record
  why the selected mode is proportional to the project's risk and scope.

Acceptance-Criteria:
  - `docs/PROJECT_BRIEF.md` names the problem, operator, proof metric, current
    workaround, AI/model cost exposure, and external skill exposure.
  - The selected mode is recorded in this file and in the handoff prompt.
  - Any omitted heavy artifact is explicitly marked optional or not applicable.

Verification:
  - manual review of `docs/PROJECT_BRIEF.md`

### T02: Establish Verification Baseline

Owner: codex
Phase: 1
Type: test
Status: planned

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
