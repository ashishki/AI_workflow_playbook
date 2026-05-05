# Skill Interface — Code Simplification Pass

Status: EXPERIMENTAL — see §8 Experiment E5 in the integration assessment.
Maintainer: Playbook maintainers

## Purpose

A user-triggered review pass that identifies redundant abstraction, dead
code, over-comment density, and other complexity bloat — and converts
approved findings into normal Codex tasks with behavior-preserving
acceptance criteria. The mandatory deep review cycle catches contract
violations and security issues; this pass catches "the code is correct
but unnecessarily complex". They are complementary, not overlapping.

## Trigger

- Explicit user invocation, e.g. via
  `templates/.claude/commands/simplify.md`.
- NEVER automatic. NEVER part of the mandatory phase-boundary cycle.

## Allowed Role

| Role | Allowed |
|------|---------|
| Strategist | no — Strategist plans architecture, not refactors |
| Orchestrator | no — does not own this pass |
| Reviewer (specialized: simplification) | yes |
| Human | yes — initiates the pass and approves the report |
| Codex (implementation agent) | never directly — Codex implements the approved findings as normal tasks |

## Forbidden Actions

- does not write application code; approved findings become normal Codex
  tasks
- does not modify `docs/IMPLEMENTATION_CONTRACT.md`,
  `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md` directly
- does not produce findings that change behavior — those are REJECTED in
  the report
- does not relax security, observability, or capability-profile rules
- does not close existing review findings or alter the deep review cycle
- does not drop tests
- does not remove TODOs that reference open findings or active tasks

## Input Artifacts

- user-stated scope (file/dir list) — required
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/dev-standards.md` (if present)
- current test baseline (must be captured before any finding is recorded)
- current complexity baseline (radon, lizard, or equivalent)
- `docs/audit/META_ANALYSIS.md` (optional fallback for scope)

## Output Artifacts

- `docs/audit/SIMPLIFICATION_REPORT.md` (overwrite per pass; row prefix
  `SIMP-N` so it does not collide with `CYCLE-N`)

The skill never writes to canonical artifacts. Approved findings reach
the codebase only via normal Codex tasks added to `docs/tasks.md` after
the human approves the report.

## Evaluation Criteria

Per §8 Experiment E5:

- LOC drops ≥10% **or** maintainability index improves ≥5 points across
  the simplified scope
- zero test regressions
- zero new P0 or P1 review findings introduced by the simplification
  tasks
- no new finding contradicts an existing open finding

If any of the above fails on a sample of phases, tighten the prompt or
remove the skill.

## Conflict Rules

Default precedence (skill output is lowest):

1. `docs/IMPLEMENTATION_CONTRACT.md` (highest)
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/spec.md`
5. `docs/tasks.md`
6. `docs/audit/SIMPLIFICATION_REPORT.md` (lowest)

A simplification finding that conflicts with a contract rule, profile
rule, or open review finding is REJECTED, not deferred. The contract
always wins.

## Review Path

- the Simplification Reviewer produces the report
- the human reads the report and approves a subset of findings
- approved findings become normal Codex tasks with behavior-preserving
  acceptance criteria (existing tests pass; new pinning test if
  required; complexity metric improves by the stated delta)
- the tasks run through normal Codex dispatch and normal light/deep
  review
- subsequent passes overwrite `docs/audit/SIMPLIFICATION_REPORT.md`

## Companion Prompt

`prompts/audit/PROMPT_SIMPLIFY.md`

## Companion Command

`templates/.claude/commands/simplify.md`
