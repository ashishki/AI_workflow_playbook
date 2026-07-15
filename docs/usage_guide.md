# Usage Guide

This guide explains how to use AI Workflow Playbook in practice for:

1. a new repository
2. an already existing repository

## Current Recommended Launch Path

Use a brief-first launch when the human will fill the project brief manually.
The deterministic initializer runs only after the human approves the filled
brief. The older slash-command bootstrap flows are still useful as Claude Code
entrypoints for Standard/Strict projects, but they should not replace the
initializer, validator, receipts, or project readiness answers.

### Current Execution Model: Codex Direct

The currently supported default is **Codex Direct**:

- the human opens a Codex session in the target repository;
- Codex reads the copied Playbook files and the approved project brief;
- Codex runs shell commands, initializer commands, validators, and tests
  directly from the active session;
- Codex must not spawn a nested Codex process with `codex exec`, `codex run`,
  or another Codex CLI invocation from inside that active Codex session.

`codex exec` examples in this repository are external-orchestration examples
only: CI, the standalone harness command adapter, or a separate non-Codex
orchestrator process may use them from outside the active Codex session. They
are not the bootstrap path for a Codex Direct project.

### Human-Filled Brief Gate

This is the safest default for a fresh repository.

Assume the Playbook is available as a Git checkout:

```bash
PLAYBOOK=/path/to/AI_workflow_playbook
PROJECT=/path/to/new-project
```

#### Stage 1 - Copy Intake Pack Only

Run this from the fresh target repository:

```bash
cd "$PROJECT"
mkdir -p docs

cp "$PLAYBOOK/templates/PROJECT_BRIEF.md" docs/PROJECT_BRIEF.md
cp "$PLAYBOOK/docs/project_fit_guide.md" docs/project_fit_guide.md
cp "$PLAYBOOK/docs/adoption_modes.md" docs/adoption_modes.md
cp "$PLAYBOOK/docs/usage_guide.md" docs/usage_guide.md
```

Then stop. The human fills:

```text
docs/PROJECT_BRIEF.md
```

Do not copy the full Playbook kit yet. Do not run the initializer yet. Do not
write application code yet.

A valid brief must contain concrete answers for:

- project name
- operational pain
- current workaround
- first proof metric
- verification command
- expected AI/model usage
- external tools/skills expected
- risk level or enough risk context to choose Lean-Core, Standard, or Strict

The human approval message should be explicit:

```text
BRIEF APPROVED
Mode: lean-core | standard | strict
Verification command: ...
Install Claude hooks: yes | no
Optional flags: cost-architecture/router-eval/cost-adapter/external-skill none|...
```

For Codex Direct, use `Install Claude hooks: no` unless the human explicitly
chooses the legacy/external Claude Code orchestration path.

#### Stage 1 Agent Prompt

Use this prompt with Codex in the target repository:

```text
You are preparing a fresh repository for AI Workflow Playbook adoption.

Current repository is the target project.
Playbook source Git checkout is:
/path/to/AI_workflow_playbook

Execution model: Codex Direct.
If you are Codex, do not invoke `codex exec`, `codex run`, or any nested Codex
CLI. You are the active bootstrap agent; run shell commands directly.

Do not write application code.
Do not run the initializer.
Do not copy the full Playbook kit.

Copy only the intake pack from the Playbook Git checkout:
- templates/PROJECT_BRIEF.md -> docs/PROJECT_BRIEF.md
- docs/project_fit_guide.md -> docs/project_fit_guide.md
- docs/adoption_modes.md -> docs/adoption_modes.md
- docs/usage_guide.md -> docs/usage_guide.md

After copying, stop and report that the human must fill docs/PROJECT_BRIEF.md.
Do not continue until the human sends BRIEF APPROVED.
```

#### Stage 2 - Bootstrap After Approval

After the human fills and approves `docs/PROJECT_BRIEF.md`, run the initializer
from the Playbook Git checkout against the target repository.

Lean-Core example:

```bash
python3 "$PLAYBOOK/tools/init_playbook_project.py" . \
  --mode lean-core \
  --project-name "Project Name" \
  --operational-pain "Concrete pain from docs/PROJECT_BRIEF.md" \
  --current-workaround "Current workaround from docs/PROJECT_BRIEF.md" \
  --first-proof-metric "First proof metric from docs/PROJECT_BRIEF.md" \
  --verify-argv '["{python}", "-m", "pytest", "-q"]'
```

Standard with legacy/external Claude hooks:

```bash
python3 "$PLAYBOOK/tools/init_playbook_project.py" . \
  --mode standard \
  --project-name "Project Name" \
  --operational-pain "Concrete pain from docs/PROJECT_BRIEF.md" \
  --current-workaround "Current workaround from docs/PROJECT_BRIEF.md" \
  --first-proof-metric "First proof metric from docs/PROJECT_BRIEF.md" \
  --verify-argv '["{python}", "-m", "pytest", "-q"]' \
  --install-claude-hooks
```

The initializer skips existing files by default, so a filled
`docs/PROJECT_BRIEF.md` is not overwritten unless `--force` is explicitly used.
Do not use `--force` during bootstrap unless the human explicitly approves
overwriting files.

Then validate:

```bash
python3 tools/playbook_validate.py --root .
python3 tools/verify_project.py --root .
```

#### Stage 2 Agent Prompt

Use this prompt with Codex only after the human has approved the filled brief:

```text
The human has approved docs/PROJECT_BRIEF.md.

Current repository is the target project.
Playbook source Git checkout is:
/path/to/AI_workflow_playbook

Execution model: Codex Direct.
If you are Codex, do not invoke `codex exec`, `codex run`, or any nested Codex
CLI. You are the active bootstrap agent; run shell commands directly.

Do not write application code yet.
Do not use --force.

Read:
- docs/PROJECT_BRIEF.md
- docs/project_fit_guide.md
- docs/adoption_modes.md
- docs/usage_guide.md

Extract:
- project name
- selected mode from the human approval
- operational pain
- current workaround
- first proof metric
- verification command
- whether Claude hooks should be installed
- optional initializer flags

If any required value is missing, stop and ask the human. Do not invent it.

Run /path/to/AI_workflow_playbook/tools/init_playbook_project.py against this
repository with those values.

After initialization, run:
python3 tools/playbook_validate.py --root .
python3 tools/verify_project.py --root .

Do not claim success unless both commands pass.
Report:
- selected mode
- generated or skipped files
- validation result
- verification result
- next recommended task
```

### New Lean-Core Project

Lean-Core is the default starting point when the project only needs task
discipline, a compact contract, and one runnable verification path.

```bash
python3 /path/to/AI_workflow_playbook/tools/init_playbook_project.py \
  /path/to/new-project \
  --mode lean-core \
  --project-name "New Project" \
  --operational-pain "Name the concrete workflow pain." \
  --current-workaround "Name how the team handles it today." \
  --first-proof-metric "Name the first measurable proof." \
  --verify-argv '["{python}", "-m", "pytest", "-q"]'
```

Then verify the generated project:

```bash
cd /path/to/new-project
python3 tools/playbook_validate.py --root .
python3 tools/verify_project.py --root .
```

### New Standard Or Strict Project

Use Standard when the project has a recoverable product workflow. Use Strict for
PII, compliance, privileged tools, persistent agents, destructive actions, or
high-cost/hard-to-reverse changes.

```bash
python3 /path/to/AI_workflow_playbook/tools/init_playbook_project.py \
  /path/to/new-project \
  --mode standard \
  --project-name "New Project" \
  --operational-pain "Name the concrete workflow pain." \
  --current-workaround "Name how the team handles it today." \
  --first-proof-metric "Name the first measurable proof." \
  --verify-argv '["{python}", "-m", "pytest", "-q"]' \
  --install-claude-hooks
```

Add optional capabilities only when they are actually in scope:

```bash
--with-cost-architecture
--with-router-eval
--with-cost-adapter
--external-skill "skill-name"
```

`--install-claude-hooks` safely merges `.claude/settings.json`, copies hook
scripts, makes them executable, and runs a hook smoke test. If the smoke test
fails, the initializer returns a non-zero exit. Without this flag, hooks are
available but not active enforcement. In Codex Direct mode, leave this flag off
unless the human intentionally enables the legacy/external Claude Code path.

### Existing Repository Retrofit

Do not fake a greenfield Phase 1. Run the initializer from inside the existing
repository with the real verification command for that stack:

```bash
cd /path/to/existing-project
python3 /path/to/AI_workflow_playbook/tools/init_playbook_project.py \
  . \
  --mode lean-core \
  --project-name "Existing Project" \
  --operational-pain "Name the real pain in this existing repo." \
  --current-workaround "Name the current workaround or manual process." \
  --first-proof-metric "Name the first proof that adoption helped." \
  --verify-argv '["{python}", "-m", "pytest", "-q"]'
```

Use the project's real command:

```bash
--verify-argv '["npm", "test"]'
--verify-argv '["pnpm", "test"]' --verify-argv '["pnpm", "lint"]'
--verify-argv '["make", "test"]'
--verify-argv '["cargo", "test"]'
```

Then verify:

```bash
python3 tools/playbook_validate.py --root .
python3 tools/verify_project.py --root .
```

The first task after retrofit should be the first real incomplete task, not a
fake skeleton task unless the repository genuinely lacks a usable skeleton.

### Legacy Claude Code Operating Pattern

This is a legacy/external orchestration path, not the current Codex Direct
default. Use it only when the project intentionally runs Claude Code as the
orchestrator and Codex as a separate external implementation process. Claude
should read:

- `AGENTS.md` or `docs/CODEX_PROMPT.md`
- `docs/tasks.md`
- `docs/CONTRACT_LITE.md` or `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/adoption_modes.md`

Claude's job is to select the next task, prepare the Codex prompt, inspect
receipts and validator output, and enforce review boundaries. Claude should not
treat an agent's prose summary as evidence that tests passed.

If you use Claude Code slash commands, `/bootstrap-new` and
`/bootstrap-retrofit` are entrypoints for generating or organizing the package.
After that, the deterministic checks above are still required.

### Codex Direct Operating Pattern

Use Codex as the active implementation agent. Do not ask Codex to call
`codex exec` inside itself; the current Codex session is already the execution
agent. A minimal task prompt is:

```text
Read AGENTS.md, docs/tasks.md, and docs/CONTRACT_LITE.md.
Pick the next planned task or use the task ID I provide.
Make the minimal implementation.
Run shell commands directly, including the declared test or verification
command.
Do not claim success without command evidence.
If verification fails, fix within the correction budget or report BLOCKED.
```

Before implementation, classify test-first applicability as `required`,
`optional`, or `not_applicable` using
`docs/testing/test_first_protocol.md`. Required work demonstrates the smallest
useful public executable spec failing for the intended reason, makes it pass,
and then runs broader project verification. Optional or non-applicable work
records why and still runs a concrete verifier; it does not skip evidence.

Public specs guide the implementation loop. They do not replace CI, capability
evaluation, runtime verification, review, or human approval.

For higher-risk tasks, run verification through a command receipt:

```bash
python3 tools/receipt_run.py \
  --task-id T01 \
  --output-dir reports/receipts/T01 \
  -- pytest -q
```

The receipt records stdout/stderr artifacts, hashes, exit code, Git state, and
environment summary. It does not assign `passed`, `verified`, or
`release_ready`.

### Readiness And Delivery Contracts

Generated projects include `.playbook/readiness_state.json` and
`.playbook/delivery_execution_model.json`.

`readiness_state.json` starts at `scaffold`. The initializer may preserve
generated scaffold placeholders, but `tools/playbook_validate.py --check
readiness` blocks `implementation_ready` and `release_ready` while those markers
remain in active artifacts. `release_ready` also requires
`.playbook-artifacts/project_verification.json` with `required_failures=0`, a
`project_commit` matching current `HEAD`, and no dirty Git state outside
`.playbook-artifacts/`. Required decisions are mode/profile/risk-triggered, not
every universal template row.

`delivery_execution_model.json` records the active delivery profile. The default
is `solo_verified`: one active Codex session may implement, deterministic
verification must pass, and human or independent review gates still apply by risk
policy. `tools/playbook_validate.py --check delivery` blocks self-completion
authority, missing reviewer authority, missing `tools/verify_project.py`
verifier binding, missing review triggers, and missing Codex Direct binding.
External `codex exec` remains for CI, harness runs, or a separate non-Codex
orchestrator process.

### Harness And Evaluation

The companion harness is not required for ordinary Lean-Core or Standard use.
Use it when you need evidence that a Playbook workflow improves false-success,
policy compliance, recovery, or regression behavior.

The bundled `playbook_core_v1` suite proves the mechanism works. It is not proof
for your product. A project-specific benchmark needs project-specific fixtures,
traps, independent scorers, pass/fail rules, and baseline vs Playbook-Min
prompts.

Every harness trial emits `harness_eval_unit.json`, and each EvidenceBundle
references it. Comparison checks a compatibility fingerprint covering model,
adapter, tool/memory/permission policy, environment, scorer set, timeout/retry
policy, dataset version, and delivery profile. Prompt hashes are recorded but not
forced identical because baseline and candidate prompts are expected to differ.
For real-model comparisons, run with `--empirical-comparison` and supply
`--provider`, `--model-id`, `--cli-version`, `--reasoning-profile`,
`--permission-policy`, and `--delivery-profile`; unknown identity is accepted
only for scripted/mechanism demonstrations.

Recommended real-command comparison shape:

The `codex exec` template below is for an external harness process. Do not run
it from inside an active Codex Direct project session.

```bash
harness-lab run \
  --suite path/to/project_suite \
  --condition baseline \
  --adapter command \
  --command-template 'codex exec -s workspace-write "$(cat {prompt_file})"' \
  --trials 3 \
  --output runs/baseline \
  --fail-on-invalid-run

harness-lab run \
  --suite path/to/project_suite \
  --condition playbook \
  --adapter command \
  --command-template 'codex exec -s workspace-write "$(cat {prompt_file})"' \
  --trials 3 \
  --output runs/playbook \
  --fail-on-invalid-run

harness-lab compare \
  --baseline runs/baseline \
  --candidate runs/playbook \
  --output reports/comparison \
  --fail-on-invalid-run \
  --fail-on-hard-gate
```

Do not run paid or networked model experiments until the model, provider,
adapter, permission profile, timeout, retry policy, trial count, and budget are
fixed.

## Cheat Sheet

### 1. Choose Mode

1. Check project fit with `docs/project_fit_guide.md`.
2. Select Lean, Standard, or Strict using `docs/adoption_modes.md`.
3. Declare the AI/model budget boundary if the project uses LLMs, agents,
   dynamic workflows, recurring evals, or multi-agent review.
4. Add cost architecture when AI usage is recurring/material or uses prompt
   caching, batch lanes, dynamic routing, or cascades.
5. If external skills are planned, create an external skill trust record before
   install/enablement.
6. Copy only the artifacts required by that mode.
7. Run the Phase 1 validator in that mode.
8. Start the orchestrator or the Lean task/review loop.

### Lean Repository

1. Create `docs/tasks.md`.
2. Create a short `docs/CODEX_PROMPT.md` or `AGENTS.md`.
3. Create a contract-lite implementation boundary.
4. Add CI or a documented local verification command.
5. Add an inline budget boundary for any AI/model work.
6. Add inline cost architecture notes when AI/model usage is recurring,
   materially costly, cache-aware, routed, or cascaded.
7. Add inline external-skill trust notes for any project-local instruction-only
   skill, or a full trust record for any external/executable skill.
8. Use deterministic or light review at meaningful boundaries.

### Standard / Strict Repository

1. Prefer the initializer:
   `python3 AI_workflow_playbook/tools/init_playbook_project.py <target> --mode standard --operational-pain "..." --current-workaround "..." --first-proof-metric "..."`.
2. If bootstrapping manually, copy `PLAYBOOK.md`, `prompts/`, `templates/`,
   `hooks/`, `ci/ci.yml`, `tools/`, and `schemas/`.
3. Copy the appropriate Claude/Codex entrypoint if your agent surface uses one.
4. Make `hooks/*.sh` executable.
5. Run `/bootstrap-new`, `/bootstrap-retrofit`, or the Codex equivalent prompt.
6. Run the Phase 1 validator in Standard or Strict mode.
7. Add `docs/COST_BUDGET.md` when recurring AI usage, agent loops, dynamic
   workflows, multi-user AI features, or material inference cost exist.
8. Add `docs/ai_cost_architecture.md` when AI spend is recurring/material,
   prompt caching or batch lanes are used, or routing/cascades affect quality
   and cost.
9. Add `docs/router_eval.md` before dynamic routing or cascades.
10. Add `docs/security/skills/{skill-name}/TRUST_RECORD.md` before installing
    or enabling any third-party/cross-project skill.
11. Start the orchestrator.

### Existing Repository

For an existing repository, do not fake a greenfield Phase 1. Select a mode,
capture current state, and start from the first real incomplete task.

### Remember

- project fit = problem-first gate
- adoption mode = overhead budget
- AI/model budget = cost guardrail before recurring agent work
- AI cost architecture = technical plan for reducing spend without losing quality
- external skill trust record = security gate before third-party skills enter
  the agent context
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
- workload classes, cache/batch strategy, routing maturity, and cascade rules
  when AI spend is recurring/material or routing/caching is part of the design
- external skills, their source, install scope, declared capabilities, and
  whether scan/signature/hash evidence is required

If those answers are weak, use Lean mode or start with discovery, measurement,
a deterministic script, a CI gate, or a review checklist instead of the full
playbook.

## New Repository

### Optional Claude Code entrypoint for Standard/Strict

Prefer `init_playbook_project.py --install-claude-hooks`. Use the manual steps
below only when you intentionally are not using the initializer.

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

Prefer the deterministic initializer:

```bash
python3 /path/to/AI_workflow_playbook/tools/init_playbook_project.py \
  /path/to/target-project \
  --mode standard \
  --project-name "Target Project" \
  --operational-pain "Name the concrete workflow pain." \
  --current-workaround "Name how the team handles it today." \
  --first-proof-metric "Name the first measurable proof." \
  --with-cost-architecture \
  --with-cost-adapter
```

Add `--external-skill NAME` before installing a third-party skill. Add
`--with-router-eval` before dynamic routing or cascades. The initializer skips
existing files by default; use `--force` only when you intentionally want to
replace generated artifacts. It rejects empty, `unknown`, `TBD`, or `TODO`
readiness values so generated projects do not pass placeholder checks with fake
project-fit evidence.

Manual fallback: copy only the selected mode's kit into the target repo.

Lean:

- `docs/project_fit_guide.md`
- `templates/tasks_schema.md`
- `docs/cost_budget_guardrails.md`
- `docs/cache_context_layout.md` when prompt caching is used
- `docs/external_skill_security_policy.md` when external skills are planned
- `docs/cost_telemetry_protocol.md`
- a short `docs/CODEX_PROMPT.md` or `AGENTS.md`
- a contract-lite implementation boundary
- `templates/COST_BUDGET.md` when AI/model budget needs a dedicated artifact
- `templates/COST_ARCHITECTURE.md` when AI/model cost architecture needs a
  dedicated artifact
- `templates/ROUTER_EVAL.md` when dynamic routing or cascades are planned
- `templates/EXTERNAL_SKILL_TRUST_RECORD.md` when external skills are planned
- `templates/COST_TELEMETRY_ADAPTER.md` when thresholds need a project-owned
  provider boundary
- `templates/cost_adapters/` when the project wants a starter telemetry adapter
- `tools/cost_rollup.py`, `tools/integrity_check.py`, and
  `tools/skill_security_gate.py` when CI/review should enforce artifacts
- CI or a documented local verification command

Standard/Strict:

- `PLAYBOOK.md`
- `docs/project_fit_guide.md`
- `prompts/`
- `templates/`
- `hooks/`
- `ci/ci.yml`
- `docs/cost_budget_guardrails.md`
- `docs/cache_context_layout.md`
- `docs/external_skill_security_policy.md`
- `docs/cost_telemetry_protocol.md`
- `templates/COST_BUDGET.md`
- `templates/COST_ARCHITECTURE.md`
- `templates/ROUTER_EVAL.md`
- `templates/EXTERNAL_SKILL_TRUST_RECORD.md`
- `templates/COST_TELEMETRY_ADAPTER.md`
- `templates/cost_adapters/`
- `tools/`
- `schemas/`

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
- inline AI cost architecture notes, or `docs/ai_cost_architecture.md` when
  cost needs a dedicated architecture artifact
- inline external-skill trust notes, or
  `docs/security/skills/{skill-name}/TRUST_RECORD.md` before any external
  skill is installed/enabled
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
- `docs/ai_cost_architecture.md` generated from
  `templates/COST_ARCHITECTURE.md` when AI spend is recurring/material,
  prompt caching or batch lanes are used, or routing/cascades affect cost and
  quality
- `docs/router_eval.md` when dynamic routing or cascades are used
- `docs/security/skills/{skill-name}/TRUST_RECORD.md` when third-party,
  marketplace, vendor, GitHub, zip, or cross-project skills are installed,
  enabled, updated, or planned
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

This is for the legacy/external Claude Code orchestration path. For Codex
Direct bootstrap, do not install Claude hooks unless the human explicitly asks
for that separate path.

### 4. Validate Phase 1

Run the Phase 1 validator before any implementation task.

Set `Mode: Lean`, `Mode: Standard`, or `Mode: Strict`. Do not begin work until
mode-relevant blockers are resolved.

### 5. Start the Orchestrator

For Codex Direct, skip the Claude orchestrator and continue in the active Codex
session using the approved brief, `AGENTS.md`, `docs/tasks.md`, and the project
verification command.

For the legacy/external Claude Code path only, open Claude Code with
`docs/prompts/ORCHESTRATOR.md`.

The orchestrator should:

- read current repo state
- validate tags and drift
- choose the next task
- enforce the right review path

## Existing Repository

### Principle

Do not fake greenfield.

Retrofit the playbook onto the current repo reality instead of pretending the project is starting from zero.

### Optional Claude Code entrypoint for Standard/Strict

Prefer `init_playbook_project.py --install-claude-hooks`. If you are doing a
manual Standard/Strict retrofit with Claude Code, copy:

1. read `docs/project_fit_guide.md`
2. `templates/.claude/settings.json` -> `.claude/settings.json`
3. `templates/.claude/commands/bootstrap-retrofit.md` -> `.claude/commands/bootstrap-retrofit.md`
4. `hooks/*.sh`

Then run:

`/bootstrap-retrofit`

This lets Claude start the retrofit flow as a command without changing the system prompt.

### 1. Add the governance kit

Manual fallback only. The initializer handles the proportional copy path for
normal use. If bootstrapping manually, copy:

- `PLAYBOOK.md`
- `docs/project_fit_guide.md`
- `docs/adoption_modes.md`
- `docs/cost_budget_guardrails.md`
- `docs/cache_context_layout.md`
- `docs/external_skill_security_policy.md`
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
- `docs/ai_cost_architecture.md` when the repo has recurring/material AI
  usage, prompt caching, batch lanes, model tiering, dynamic routing, or
  cascades. Lean retrofits may keep this inline if the scope is small.
- `docs/router_eval.md` when existing dynamic routing or cascades are kept.
- `docs/security/skills/{skill-name}/TRUST_RECORD.md` when existing external
  skills are kept. If evidence is missing, create a `Type: skill:security`
  remediation task before enabling the skill in new agent sessions.
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
9. cost architecture for recurring/material usage, prompt caching, batch lanes,
   routing, or cascades
10. cost telemetry rollup when usage is recurring or thresholds exist
11. router eval only when dynamic routing or cascades are actually used
12. external skill trust records before third-party skills are installed or
   enabled
13. audit prompts
14. orchestrator loop
15. filesystem reality and runtime verification for risky writes
16. hooks for codex-only code writes and phase-boundary guards
17. integrity checks for Context-Refs, evidence, README indexes, and cognition packets
18. selective heavy-task mode + evidence index
19. packaging

This order preserves momentum while tightening governance over time.

## What Command-Based Bootstrap Does And Does Not Do

This section describes the legacy/external Claude Code command flow. It is not
the current Codex Direct bootstrap path.

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

Set `CURRENT_TASK` before task-scoped shell work to annotate hook logs with the
active task ID.

In Codex Direct mode, run commands directly from the active Codex session:

```bash
export CURRENT_TASK="T07"
cd /path/to/project
pytest -q
```

Do not invoke nested `codex exec` from inside Codex Direct. Legacy external
orchestrators may still set `CURRENT_TASK` before launching their separate
implementation process.

The log at `docs/hooks_log.txt` will then show:

```
[2026-04-03T12:00:00Z] [TASK:T07] EXIT=0      pytest tests/ -q
[2026-04-03T12:00:01Z] [TASK:T07]   └─ IMPLEMENTATION_RESULT: DONE
```

This is included in the legacy `ORCHESTRATOR.md` Execute block template for
external orchestration. In Codex Direct mode, set the task ID in the active
session before running the task's verification commands.

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
