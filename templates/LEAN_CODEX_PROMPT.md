# CODEX_PROMPT.md

Mode: Lean
Version: 1.0
Date: {{DATE}}

## Current State

- Phase: 1
- Baseline: pre-implementation
- Verification command:
- Last verification:
- Cost budget:
- Cost architecture:
- External skills:

## Next Task

T01:

## Fix Queue

empty

## Open Findings

none

## Instructions for Codex

1. Read the current task in `docs/tasks.md`.
2. Read `docs/CONTRACT_LITE.md` or the project contract-lite section.
3. Read only the files listed in the task unless verification shows more context
   is required.
4. Before editing, run or record the baseline verification command when it
   exists.
5. Keep changes inside the declared file scope.
6. Add or update tests when behavior changes.
7. Run the task's `test:` or `verify:` command.
8. Record changed files, verification output, and any budget/cost issue.
9. Stop before installing/enabling/updating external skills unless trust
   evidence is already present or the task is explicitly creating it.
10. Return `IMPLEMENTATION_RESULT: DONE` only when repository state supports the
    claim.

## Minimal Implementation Rules

These rules apply to implementation and fix work, not to the completeness of
review, audit, security, or evidence reports.

Before adding an artifact:

1. Skip it when the requested behavior does not require it.
2. Reuse an existing repository helper, contract, file, or execution path.
3. Prefer the standard library or a native platform capability.
4. Prefer an already-installed dependency over adding another one.
5. Extend the authoritative path instead of creating a parallel path.
6. Write only the smallest change that proves the requested behavior.

- No abstraction without a current second consumer.
- No compatibility layer without a real supported legacy consumer.
- No new file when an existing cohesive file can own the responsibility.
- Every new test must protect a distinct invariant, regression, trust boundary,
  or acceptance condition; merge near-identical cases parametrically.
- Bug fixes should reproduce the failure before changing production behavior.
- Prefer deletion and consolidation over scaffolding for hypothetical future use.
- Never remove trust-boundary validation, security, accessibility, data-loss
  handling, evidence integrity, human approval, or release gates for brevity.

## Cost / Budget Notes

- Prefer deterministic scripts before model calls.
- Use the minimum sufficient model.
- Stop before exceeding the declared per-task budget.
- Escalate if a loop, retry storm, or broad file search starts consuming budget
  without new evidence.
- For recurring/material AI usage, write the workload class, output cap,
  retry/fan-out cap, cache/batch/routing decision, and escalation rule here or
  in `docs/ai_cost_architecture.md`.
- Dynamic routing or cascades require `docs/router_eval.md`; do not rely on a
  cheap model's self-confidence as the only escalation judge.

## External Skill Notes

- Instruction-only, project-local skills may record trust evidence inline.
- Third-party/cross-project, executable, networked, MCP/tool-enabled,
  file/env-accessing, persistent, or global skills require
  `docs/security/skills/{skill-name}/TRUST_RECORD.md`.
