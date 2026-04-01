# Usage Guide

This guide explains how to use AI Workflow Playbook in practice for:

1. a new repository
2. an already existing repository

## New Repository

### Fastest Claude Code entrypoint

If you are using Claude Code, you do not need to replace the system prompt manually every time.

Recommended setup:

1. copy `templates/.claude/settings.json` to `.claude/settings.json`
2. copy `templates/.claude/commands/bootstrap-new.md` to `.claude/commands/bootstrap-new.md`
3. copy `hooks/*.sh`
4. make hooks executable

Then in Claude Code you can run:

`/bootstrap-new`

This command works as a user-level entrypoint. It tells Claude which local files to read and how to bootstrap the Phase 1 package.

### 1. Prepare the kit

Copy into the target repo:

- `PLAYBOOK.md`
- `prompts/`
- `templates/`
- `hooks/`
- `ci/ci.yml`

### 2. Run the Strategist

Use:

- `prompts/STRATEGIST.md`
- your filled project brief

If you are using the command flow, `/bootstrap-new` performs this same entry step without you manually pasting the strategist prompt first.

The output should create the initial governance package:

- `docs/ARCHITECTURE.md`
- `docs/spec.md`
- `docs/tasks.md`
- `docs/CODEX_PROMPT.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
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

Do not begin work until blockers are resolved.

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

### Fastest Claude Code entrypoint

If you are using Claude Code, copy:

1. `templates/.claude/settings.json` -> `.claude/settings.json`
2. `templates/.claude/commands/bootstrap-retrofit.md` -> `.claude/commands/bootstrap-retrofit.md`
3. `hooks/*.sh`

Then run:

`/bootstrap-retrofit`

This lets Claude start the retrofit flow as a command without changing the system prompt.

### 1. Add the governance kit

Copy:

- `PLAYBOOK.md`
- `prompts/`
- `templates/`
- `hooks/`
- `ci/ci.yml` if CI is missing or needs normalization

### 2. Build the current-state docs

Generate:

- `docs/ARCHITECTURE.md` from the system as it exists now
- `docs/spec.md` for current supported behavior plus near-term intended scope
- `docs/CODEX_PROMPT.md` with the real current baseline and next task
- `docs/IMPLEMENTATION_CONTRACT.md` from stable rules the repo should obey going forward

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

### 5. Use heavy tasks selectively

Only tasks with materially higher risk should carry the optional heavy-task extension.

### 6. Start from the real next task

The first task after retrofit should be the first real incomplete task, not a fake skeleton task unless the repo genuinely still lacks a usable skeleton.

## Practical Adoption Order

If you want to introduce the playbook gradually:

1. task schema
2. implementation contract
3. CODEX_PROMPT resumable state
4. audit prompts
5. orchestrator loop
6. selective heavy-task mode
7. hooks and packaging

This order preserves momentum while tightening governance over time.

## What Command-Based Bootstrap Does And Does Not Do

What it does:

- gives Claude a standard entrypoint
- tells it which local files to read
- tells it which artifact set to generate
- keeps startup UX simple

What it does not do:

- it does not replace the need for clarification questions
- it does not magically validate Phase 1 by itself
- it does not replace the orchestrator

The best mental model is:

- slash command = bootstrap entrypoint
- validator = artifact gate
- orchestrator = control-plane for ongoing work
