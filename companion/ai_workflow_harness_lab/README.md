# AI Workflow Harness Lab

Standalone companion package for running reproducible baseline-vs-Playbook
workflow evaluations.

This package is intentionally separate from the core Playbook. It consumes
Playbook schemas and files, but it does not import root Playbook Python modules
and is not required for Lean/Standard/Strict adoption.

## Commands

```bash
harness-lab validate-suite suites/playbook_core_v1

harness-lab run \
  --suite suites/playbook_core_v1 \
  --condition baseline \
  --adapter scripted \
  --trials 1 \
  --output runs/baseline

harness-lab run \
  --suite suites/playbook_core_v1 \
  --condition playbook \
  --adapter scripted \
  --trials 1 \
  --output runs/playbook

harness-lab run \
  --suite suites/playbook_core_v1 \
  --condition playbook \
  --adapter command \
  --command-template 'codex exec -s workspace-write "$(cat {prompt_file})"' \
  --trials 3 \
  --output runs/playbook-codex

harness-lab verify-bundle runs/playbook/task/trial-0/bundle.json

harness-lab compare \
  --baseline runs/baseline \
  --candidate runs/playbook \
  --output reports/comparison \
  --fail-on-invalid-run \
  --fail-on-hard-gate
```

The scripted adapter is for CI and mechanism tests. It is not evidence that the
Playbook improves real LLM behavior. Real-model runs require an installed CLI,
credentials, and an explicit budget.

Command-adapter examples are launched by an external shell, CI job, or harness
worker. Do not run them from inside an active Codex Direct project session,
because that would spawn nested Codex.

The command adapter propagates the real process exit code. Use
`--fail-on-invalid-run` during real experiments so missing commands, non-zero
adapter exits, timeouts, invalid evidence, and scorer failures fail the harness
pipeline. Use `--fail-on-hard-gate` with compare to fail on policy violations or
false-success above the configured thresholds.

Tasks may declare `required_verification`; the harness runs that command after
the adapter finishes and stores a separate command receipt. Scorers should use
post-state and receipts, not agent prose, as their source of truth.

## Project-Specific Suites

`suites/playbook_core_v1` demonstrates the shared Playbook evaluation
mechanism. It is not evidence that the Playbook improves a specific project.

For a product or repository claim, create a project-specific suite with:

- representative fixture repositories or task states
- baseline and Playbook-Min prompts for the same task
- traps based on the project's real failure modes
- independent scorers for protected files, command receipts, diffs, tests,
  policy boundaries, and post-state invariants
- explicit pass/fail rules and expected failure taxonomy

Scaffolded directories are acceptable as a starting point. Automatically
invented benchmark content is not acceptable evidence.

## Generic Command Adapter Examples

These commands are external adapter examples. They are not the Codex Direct
bootstrap path.

Codex:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'codex exec -s workspace-write "$(cat {prompt_file})"' \
  --trials 3 --output runs/codex-playbook
```

Claude Code:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'claude --print "$(cat {prompt_file})"' \
  --trials 3 --output runs/claude-playbook
```

OpenCode-style command:

```bash
harness-lab run --suite suites/playbook_core_v1 --condition playbook \
  --adapter command \
  --command-template 'opencode run --prompt-file {prompt_file}' \
  --trials 3 --output runs/opencode-playbook
```
