# Usage Guide

This guide explains how to use AI Workflow Playbook in practice for:

1. a new repository
2. an already existing repository

## Cheat Sheet

### 1. Choose Mode

1. Check project fit with `docs/project_fit_guide.md`.
2. Select Lean, Standard, or Strict using `docs/adoption_modes.md`.
3. Declare the AI/model budget boundary if the project uses LLMs, agents,
   dynamic workflows, recurring evals, or multi-agent review.
4. Copy only the artifacts required by that mode.
5. Run the Phase 1 validator in that mode.
6. Start the orchestrator or the Lean task/review loop.

### Lean Repository

1. Create `docs/tasks.md`.
2. Create a short `docs/CODEX_PROMPT.md` or `AGENTS.md`.
3. Create a contract-lite implementation boundary.
4. Add CI or a documented local verification command.
5. Add an inline budget boundary for any AI/model work.
6. Use deterministic or light review at meaningful boundaries.

### Standard / Strict Repository

1. Copy `PLAYBOOK.md`, `prompts/`, `templates/`, `hooks/`, `ci/ci.yml`.
2. Copy `templates/.claude/settings.json` -> `.claude/settings.json`.
3. Copy the appropriate bootstrap command.
4. Make `hooks/*.sh` executable.
5. Run `/bootstrap-new` or `/bootstrap-retrofit`.
6. Run the Phase 1 validator in Standard or Strict mode.
7. Add `docs/COST_BUDGET.md` when recurring AI usage, agent loops, dynamic
   workflows, multi-user AI features, or material inference cost exist.
8. Start the orchestrator.

### Existing Repository

For an existing repository, do not fake a greenfield Phase 1. Select a mode,
capture current state, and start from the first real incomplete task.

### Remember

- project fit = problem-first gate
- adoption mode = overhead budget
- AI/model budget = cost guardrail before recurring agent work
- slash command = optional entrypoint
- validator = mode-aware gate
- orchestrator = ongoing workflow when Standard/Strict is justified

## Before Bootstrap: Project Fit

Before generating phases, read `docs/project_fit_guide.md` and fill
`templates/PROJECT_BRIEF.md §1b Problem Fit and Adoption Reality`.

Do not begin a full agentic build until the brief names:

- the concrete operational pain
- the current workaround
- why the current process is insufficient
- the first user or operator
- the first proof metric
- which AI adoption claims are not allowed before evidence exists
- AI/model cost exposure and approval threshold, when LLMs or agents are in scope

If those answers are weak, use Lean mode or start with discovery, measurement,
a deterministic script, a CI gate, or a review checklist instead of the full
playbook.

## New Repository

### Fastest Claude Code entrypoint for Standard/Strict

If you are using Claude Code, you do not need to replace the system prompt manually every time.

Recommended setup for Standard/Strict:

1. read `docs/project_fit_guide.md`
2. copy `templates/.claude/settings.json` to `.claude/settings.json`
3. copy `templates/.claude/commands/bootstrap-new.md` to `.claude/commands/bootstrap-new.md`
4. copy `hooks/*.sh`
5. make hooks executable

Then in Claude Code you can run:

`/bootstrap-new`

This command works as a user-level entrypoint. It tells Claude which local files to read and how to bootstrap the Phase 1 package.

Lean projects may skip the command flow and create the Lean package directly
from `docs/adoption_modes.md`.

### 1. Prepare the kit

Copy only the selected mode's kit into the target repo.

Lean:

- `docs/project_fit_guide.md`
- `templates/tasks_schema.md`
- `docs/cost_budget_guardrails.md`
- `docs/cost_telemetry_protocol.md`
- a short `docs/CODEX_PROMPT.md` or `AGENTS.md`
- a contract-lite implementation boundary
- `templates/COST_BUDGET.md` when AI/model budget needs a dedicated artifact
- `templates/COST_TELEMETRY_ADAPTER.md` when thresholds need a project-owned
  provider boundary
- CI or a documented local verification command

Standard/Strict:

- `PLAYBOOK.md`
- `docs/project_fit_guide.md`
- `prompts/`
- `templates/`
- `hooks/`
- `ci/ci.yml`
- `docs/cost_budget_guardrails.md`
- `docs/cost_telemetry_protocol.md`
- `templates/COST_BUDGET.md`
- `templates/COST_TELEMETRY_ADAPTER.md`

### 2. Run the Strategist

Use:

- `prompts/STRATEGIST.md`
- your filled project brief

If you are using the command flow, `/bootstrap-new` performs this same entry step without you manually pasting the strategist prompt first.

The output should create the initial governance package for the selected mode.

Lean package:

- `docs/tasks.md`
- short `docs/CODEX_PROMPT.md` or `AGENTS.md`
- contract-lite boundary
- verification command
- review checklist
- inline AI/model budget, or `docs/COST_BUDGET.md` when budget needs a
  dedicated artifact
- `docs/ai_cost_telemetry.jsonl` and `reports/ai_cost_rollup.md` when recurring
  AI usage needs telemetry evidence

Standard/Strict package:

- `docs/ARCHITECTURE.md`
- `docs/README.md` as the README-first index for project docs
- `docs/spec.md`
- `docs/tasks.md`
- `docs/CODEX_PROMPT.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/COST_BUDGET.md` when required by `docs/cost_budget_guardrails.md`
- cost telemetry rollup setup from `docs/cost_telemetry_protocol.md` when
  `docs/COST_BUDGET.md` declares thresholds
- `docs/DECISION_LOG.md`
- `docs/IMPLEMENTATION_JOURNAL.md`
- `docs/EVIDENCE_INDEX.md` when the project warrants an evidence index
- `docs/prompts/ORCHESTRATOR.md`
- `docs/prompts/PROMPT_S_STRATEGY.md`
- `docs/audit/*`
- `.github/workflows/ci.yml`

### 3. Wire Claude Code if needed

Recommended:

- copy `templates/.claude/settings.json` to `.claude/settings.json`
- copy `hooks/*.sh`
- make hooks executable

### 4. Validate Phase 1

Run the Phase 1 validator before any implementation task.

Set `Mode: Lean`, `Mode: Standard`, or `Mode: Strict`. Do not begin work until
mode-relevant blockers are resolved.

### 5. Start the Orchestrator

Open Claude Code with `docs/prompts/ORCHESTRATOR.md`.

The orchestrator should:

- read current repo state
- validate tags and drift
- choose the next task
- enforce the right review path

## Existing Repository

### Principle

Do not fake greenfield.

Retrofit the playbook onto the current repo reality instead of pretending the project is starting from zero.

### Fastest Claude Code entrypoint for Standard/Strict

If you are using Claude Code for a Standard/Strict retrofit, copy:

1. read `docs/project_fit_guide.md`
2. `templates/.claude/settings.json` -> `.claude/settings.json`
3. `templates/.claude/commands/bootstrap-retrofit.md` -> `.claude/commands/bootstrap-retrofit.md`
4. `hooks/*.sh`

Then run:

`/bootstrap-retrofit`

This lets Claude start the retrofit flow as a command without changing the system prompt.

### 1. Add the governance kit

Copy:

- `PLAYBOOK.md`
- `docs/project_fit_guide.md`
- `docs/adoption_modes.md`
- `docs/cost_budget_guardrails.md`
- `docs/cost_telemetry_protocol.md`
- `prompts/`
- `templates/`
- `hooks/`
- `ci/ci.yml` if CI is missing or needs normalization

### 2. Build the current-state docs

Generate:

- `README.md` or update the existing root README as the repo entry index
- `docs/README.md` as the docs index
- `docs/ARCHITECTURE.md` from the system as it exists now
- `docs/spec.md` for current supported behavior plus near-term intended scope
- `docs/CODEX_PROMPT.md` with the real current baseline and next task
- `docs/IMPLEMENTATION_CONTRACT.md` from stable rules the repo should obey going forward
- `docs/DECISION_LOG.md` seeded from the real architecture, ADRs, and unresolved tradeoffs
- `docs/IMPLEMENTATION_JOURNAL.md` starting from the retrofit session and the next real task
- `docs/EVIDENCE_INDEX.md` only if the repo already has heavy tasks, evaluation artifacts, compliance evidence, or recurring review churn
- `docs/COST_BUDGET.md` when the existing repo has recurring AI usage,
  agent loops, dynamic workflows, multi-user AI features, or material
  inference cost. Lean retrofits may keep this budget inline if the scope is
  small.
- `docs/ai_cost_telemetry.jsonl` and a `tools/cost_rollup.py` CI step when
  the repo already produces usage data or declares enforceable thresholds.

### 3. Build forward-looking tasks

Create `docs/tasks.md` as a forward contract:

- current remediation tasks
- missing governance tasks
- near-term feature tasks

Do not try to reconstruct the entire historical backlog.

### 4. Normalize the harness

Add:

- `docs/prompts/ORCHESTRATOR.md`
- audit prompts
- `.claude/settings.json` if using Claude Code hooks

For Lean retrofits, this step may be replaced by a short task/review loop and a
documented verification command.

### 5. Use heavy tasks selectively

Only tasks with materially higher risk should carry the optional heavy-task extension.

### 6. Start from the real next task

The first task after retrofit should be the first real incomplete task, not a fake skeleton task unless the repo genuinely still lacks a usable skeleton.

## Practical Adoption Order

If you want to introduce the playbook gradually:

1. project fit gate: concrete pain, current workaround, first proof metric
2. task schema
3. implementation contract
4. CODEX_PROMPT resumable state
5. decision log + implementation journal
6. README-first indexes for repo, docs, and substantial subsystem folders
7. task `Context-Refs` for history-sensitive work
8. AI/model budget boundary for recurring or agentic usage
9. cost telemetry rollup when usage is recurring or thresholds exist
10. audit prompts
11. orchestrator loop
12. filesystem reality and runtime verification for risky writes
13. hooks for codex-only code writes and phase-boundary guards
14. integrity checks for Context-Refs, evidence, README indexes, and cognition packets
15. selective heavy-task mode + evidence index
16. packaging

This order preserves momentum while tightening governance over time.

## What Command-Based Bootstrap Does And Does Not Do

What it does:

- gives Claude a standard entrypoint
- tells it which local files to read
- tells it which artifact set to generate
- surfaces optional skills after generating the package, with conditional recommendations (see below)
- keeps startup UX simple
- can enforce codex-only code writing and phase-boundary guards when the hook template is installed

What it does not do:

- it does not replace the need for clarification questions
- it does not magically validate Phase 1 by itself
- it does not replace the orchestrator

The best mental model is:

- slash command = bootstrap entrypoint
- validator = artifact gate
- orchestrator = control-plane for ongoing work

## Optional Skills

Optional, opt-in capabilities layered on the playbook. The full registry lives in `reference/optional_skills.md`. Bootstrap commands surface them automatically after generating the package.

| Skill | Status | How it activates |
|-------|--------|-----------------|
| External Tools / MCP companion | optional | Silently active when Tool-Use=ON or MCP shape detected — no confirmation needed. TOOL-6 enforces compliance at review. |
| Research Companion | EXPERIMENTAL | Bootstrap asks yes/no if a non-trivial arch or compliance choice is found without an ADR. Can also be invoked mid-project by the Strategist or reviewer. |
| Simplification Pass | EXPERIMENTAL | Always human-triggered: run `/simplify` with a file or directory scope after code exists. Produces `docs/audit/SIMPLIFICATION_REPORT.md`; approved findings become normal Codex tasks. |

Skills never modify canonical artifacts (`IMPLEMENTATION_CONTRACT.md`, `ARCHITECTURE.md`, `spec.md`, `tasks.md`, `CODEX_PROMPT.md`). Their output is always the lowest authority in the conflict hierarchy. To add a skill, follow `reference/optional_skills.md §How to Add a Skill`.

---

## Operational Knobs

Small env vars that change hook behaviour without touching code.

### Task-tagged bash logs

Set `CURRENT_TASK` before each `codex exec` invocation to annotate every bash log line with the active task ID:

```bash
export CURRENT_TASK="T07"
PROMPT=$(cat /tmp/orchestrator_codex_prompt.txt)
cd /path/to/project && codex exec -s workspace-write "$PROMPT"
```

The log at `docs/hooks_log.txt` will then show:

```
[2026-04-03T12:00:00Z] [TASK:T07] EXIT=0      pytest tests/ -q
[2026-04-03T12:00:01Z] [TASK:T07]   └─ IMPLEMENTATION_RESULT: DONE
```

This is already included in the ORCHESTRATOR.md Execute block template — fill in the task ID each time.

### Session-end notifications

Set `NOTIFICATION_TOKEN` (Telegram bot token) and `NOTIFICATION_TARGET` (chat ID) in your environment to receive a brief push when the Claude Code session ends:

```
Session ended 2026-04-03T12:00:00Z. Active: T07 — implement auth middleware. Fix Queue: 2. Resume: paste ORCHESTRATOR.md.
```

Set `SILENT=1` to suppress notification delivery for automated or cron-driven sessions. The checkpoint file is always written regardless.

### T3 projects — external runtime references

When the playbook's Phase 1 architecture decision results in a higher-autonomy
agent at T3, external runtimes such as Hermes may be evaluated as optional
solution references. The governance rules that apply to Hermes-based T3
deployments live in:

- `docs/hermes_agent_reference_policy.md` — OSS reuse gate, official source checks, and adoption boundaries
- `reference/solution_references.md` — broader external reference catalog
- `docs/dynamic_workflow_reference_policy.md` — optional executable workflow reference gate
- `templates/ARCHITECTURE.md §T3 External Runtime Reference` — Hermes-specific configuration table when Hermes is selected
- `templates/IMPLEMENTATION_CONTRACT.md §Hermes Agent — Optional T3 Runtime Reference` — AGENT-H1..H5 rules and P1/P2 thresholds

The playbook governs the **development** of a Hermes-based application. Hermes
or any other runtime is what gets built and deployed — not a replacement for the
orchestrator or any governance layer.
