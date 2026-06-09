# AGENTS.md

## Project Mode

Mode: Lean

## Working Rules

- Repository files are the source of truth.
- Read `docs/tasks.md` before implementation.
- Read `docs/CONTRACT_LITE.md` or the project contract-lite boundary before
  editing.
- Keep changes inside the task file scope.
- Run the task's `test:` or `verify:` command before completion.
- Do not self-review meaningful implementation changes.
- Stop for human approval before auth, secrets, billing, destructive actions,
  runtime expansion, or material model-cost escalation.

## Cost Rules

- Prefer deterministic checks and scripts over model calls.
- Use the smallest model/tool path that satisfies the task.
- Do not continue retry loops after repeated equivalent failures.
- Record budget/cost issues in the task or `docs/CODEX_PROMPT.md`.

## Done Means

- Changed files match the task.
- Verification command was run or the reason it could not run is recorded.
- Any behavior change has a test or explicit manual verification.
- Completion claims are backed by repository state.
