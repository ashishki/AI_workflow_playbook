# Codex Role Execution Harness v1

Status: mechanism implemented; empirical benefit is not yet claimed.

## Purpose

Codex remains the primary interactive development and orchestration environment.
The Playbook does not replace the main Codex session and does not introduce a
generic provider runtime into core governance.

This harness controls only four independent reviewer roles:

- `product_design_review`
- `program_design_review`
- `slice_review`
- `maintainability_review`

```text
Main interactive Codex
  -> Playbook Role Runner
     -> policy preflight
     -> exact prompt and context hashes
     -> fresh read-only codex exec
     -> JSONL trace and report
     -> marker and write-drift validation
     -> tamper-evident role result
  -> Feature Workflow consumes validated evidence
```

## DeepSeek Harness principles adopted

The implementation intentionally adopts only four architectural disciplines:

1. append-only, hash-chained execution events;
2. reproducible provenance for the Playbook prompt and known repository context;
3. guarded preflight -> execute -> postflight role execution;
4. fresh, role-scoped, read-only reviewer processes.

It does not adopt Cordis, an everything-is-a-plugin runtime, a database, a Web UI,
a provider marketplace, a job system, or a generic tool platform.

## Run a role

Design review:

```bash
python tools/run_codex_role.py run \
  --root . \
  --task T14 \
  --feature-id F01 \
  --model gpt-5.6-terra \
  --reasoning-effort medium \
  --role program_design_review
```

Slice review:

```bash
python tools/run_codex_role.py run \
  --root . \
  --task T14 \
  --feature-id F01 \
  --slice-id F01-S1 \
  --role slice_review
```

A validated report is published by default to:

```text
.playbook-artifacts/reports/<feature-id>/<role>.md
```

For product and program design review, the runner calls the existing
`approve_feature_design.write_design_review_record()` consumer so design approval
remains bound to the exact reviewed Feature Design hashes.

## Generated artifacts

```text
.playbook-artifacts/runs/<run-id>/
  prompt.md
  context_manifest.json
  codex_events.jsonl
  codex_stderr.txt
  report.md
  result.json
  result.json.sha256
  events.jsonl
```

`events.jsonl` is append-only and hash-chained. It records role request, context
materialization, Codex execution, publication, and final result linkage.

`result.json` records task/feature/slice identity, base commit, Codex CLI identity,
model and reasoning effort, fixed sandbox, prompt/context/trace/report hashes,
parsed verdict, and postflight findings.

## Trust boundary

A successful process exit is not sufficient. A role result is `validated` only
when:

- the renderer produced a non-empty prompt;
- `codex exec` completed within the budget;
- JSONL trace lines are valid objects;
- a non-empty report exists;
- the required marker parses to `PASS`, `ADVISORY`, or `STOP_SHIP`;
- the reviewer changed no repository files;
- all artifacts are hash-linked.

`STOP_SHIP` is a valid reviewer result, not successful feature completion. Existing
Feature Workflow policy decides whether the work may proceed.

The runner removes parent-session Codex environment markers before starting the
child process so each reviewer receives a fresh process context. It does not remove
normal Codex authentication material.

## Verify saved evidence

```bash
python tools/run_codex_role.py verify \
  --root . \
  --result .playbook-artifacts/runs/<run-id>/result.json
```

Verification fails on artifact tampering, event-ledger hash-chain tampering, a
missing result sidecar, a result not linked from the ledger, or a different current
Git HEAD unless `--allow-head-drift` is explicitly used.

## Known capture boundary

V1 captures the exact Playbook-rendered prompt, known repository context hashes,
repository and user `AGENTS.md` identities when present, Codex CLI identity, and the
Codex JSONL execution trace.

Codex-internal system-prompt text and internal tool-schema definitions are not
currently exported by this runner. `context_manifest.json` marks those fields as
not captured instead of claiming complete reconstruction.

## Evaluation requirement

The mechanism must pass deterministic and failure-injection tests first. Its value
as the default reviewer path must then be compared with the existing manual
suggested-command route while holding model, task, repository commit, permissions,
and review policy constant.

Primary metrics:

- trace completeness;
- missing or stale evidence rate;
- wrong-sandbox and write-drift rate;
- retries and human interventions;
- prompt size, tokens, tool calls, latency, and cost per valid role result.

Hard gates:

- task/review quality is not worse;
- false completion remains zero;
- policy and scope violations remain zero;
- stale-context acceptance remains zero.

The allowed decisions remain `promote`, `accept_without_claim`, `inconclusive`, or
`reject`. No empirical improvement is claimed from mechanism tests alone.
