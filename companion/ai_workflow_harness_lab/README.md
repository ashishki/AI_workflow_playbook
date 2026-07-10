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
  --output reports/comparison
```

The scripted adapter is for CI and mechanism tests. It is not evidence that the
Playbook improves real LLM behavior. Real-model runs require an installed CLI,
credentials, and an explicit budget.

## Generic Command Adapter Examples

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
