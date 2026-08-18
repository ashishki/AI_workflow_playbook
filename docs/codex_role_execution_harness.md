# Codex Role Execution Harness v1

Status: implemented mechanism
Maturity: guarded review-role execution; empirical benefit not yet claimed

## Purpose

The main interactive Codex session remains the project orchestrator and primary
implementation surface. This harness controls only isolated review roles:

- `product_design_review`
- `program_design_review`
- `slice_review`
- `maintainability_review`

It replaces ad hoc reviewer commands with one guarded path:

```text
main Codex
→ Playbook role preflight
→ exact prompt/context materialization
→ fresh read-only codex exec
→ deterministic postflight
→ tamper-evident role result
→ Feature Workflow / human authority
```

The harness does not approve designs, accept slices, merge, push, or grant
completion authority.

## Trust Model

A process exit or reviewer statement is not sufficient evidence. A role result
is valid only when all of the following hold:

1. The role is allowed by the current deterministic review policy.
2. Task, feature, and slice identities are consistent.
3. The exact model-visible prompt is persisted and hashed.
4. Context source artifacts are recorded with content hashes.
5. Codex runs as a fresh process in `read-only` sandbox mode.
6. The JSONL trace is present and parseable.
7. The expected role marker exists in the report.
8. The reviewer did not change repository state, including a file that was
   already dirty before review.
9. Receipt, trace, report, context manifest, and event ledger hashes match the
   machine-readable role result.

## Command

Run a design review:

```bash
python3 tools/run_codex_role.py \
  --root . \
  --task T14 \
  --feature-id F01 \
  --role program_design_review
```

Run a slice review:

```bash
python3 tools/run_codex_role.py \
  --root . \
  --task T14 \
  --feature-id F01 \
  --slice-id F01-S1 \
  --role slice_review
```

Optional execution identity controls:

```bash
python3 tools/run_codex_role.py \
  --root . \
  --task T14 \
  --feature-id F01 \
  --role product_design_review \
  --model gpt-5.6-sol \
  --reasoning-effort medium \
  --timeout 900
```

Use `--dry-run` to materialize the role specification, prompt, context manifest,
and event ledger without calling Codex. Use `--replace` only for an explicit
rerun that may replace an existing report and result sidecar.

## Artifacts

Each run writes:

```text
.playbook-artifacts/runs/<run-id>/
  role_spec.json
  context_manifest.json
  prompt.md
  codex_trace.jsonl
  codex_stderr.txt
  workspace_state_delta.json
  command_receipt.json
  events.jsonl
  result.json
```

The review report remains at the policy-defined location, for example:

```text
.playbook-artifacts/reports/F01/program_design_review.md
```

A machine-readable sidecar is written beside it:

```text
.playbook-artifacts/reports/F01/program_design_review.role_run.json
```

The sidecar and canonical `result.json` use
`schemas/role_run.schema.json`. Design roles also produce the existing
hash-bound design review record under:

```text
.playbook-artifacts/reviews/<feature-id>/design/<role>.review.json
```

## Append-Only Event Ledger

`events.jsonl` records the execution sequence:

```text
role.requested
context.materialized
codex.exec.started
codex.exec.finished
role.postflight
```

The ledger indexes the execution history. It does not replace command receipts,
review records, Feature Design approval, slice acceptance, or the release
resolver.

## Model-Visible Provenance

The exact prompt sent on stdin is stored as `prompt.md`. Its SHA-256 is recorded
in both `context_manifest.json` and `result.json`. This is the authoritative
record of what the reviewer saw.

The context manifest additionally records hashes for the task file, brief,
review policy, architecture, Feature Design artifacts, and declared context
references that were available to the renderer.

## Preflight / Execute / Postflight

### Preflight

- validate role support;
- load the canonical task;
- require the task to reference the selected Feature Design;
- verify Planning Depth consistency between task and design;
- require a valid slice binding for slice roles;
- resolve the role through `feature_review_policy.py`;
- snapshot the Git workspace, including pre-existing dirty files.

### Execute

- render one bounded task/feature/slice prompt;
- start a fresh `codex exec` process;
- ignore user config and repository rules for the isolated reviewer;
- enforce `read-only` sandbox and `approval_policy=never`;
- disable web search and app/collaboration instruction injection;
- stream JSONL output to the run trace;
- write the final report to the policy-defined report path.

### Postflight

- require exit code zero;
- require a non-empty JSONL trace;
- parse the exact required report marker;
- compare full Git workspace fingerprints before and after;
- write a CommandReceipt;
- write the append-only event ledger;
- write the role result and report sidecar;
- bind design reviews to current design hashes.

`STOP_SHIP` is a valid review result and therefore has `status=validated`, but
the runner exits non-zero so orchestration stops.

## What This Does Not Do

V1 deliberately does not implement:

- main interactive Codex orchestration;
- implementer or fix-agent execution;
- session resume or fork;
- Codex App Server integration;
- generic provider routing;
- a plugin framework;
- a web interface;
- automatic repair loops;
- automatic acceptance, merge, or push.

## Evaluation Plan

The mechanism must be evaluated separately from reviewer quality.

### Experiment A: Observability

Compare the same `codex exec` review with and without role-run instrumentation.
Primary metrics:

- trace completeness;
- missing provenance rate;
- prompt/context identity recoverability;
- runtime and token overhead.

### Experiment B: Guarded Execution

Compare manual/suggested reviewer commands against `run_codex_role.py` with the
same model, task, commit, prompt policy, and sandbox intent.

Hard gates:

- false completion = 0;
- policy violations = 0;
- scope/write violations = 0;
- stale-context acceptance = 0;
- reviewer task success not worse than baseline.

Target metrics:

- missing or stale evidence;
- wrong-sandbox runs;
- invalid/missing marker runs;
- retries;
- human interventions;
- time per valid review result.

A reasonable promotion threshold is 100% trace completeness with no guardrail
regression and a material reduction in missing/stale evidence. Lower token use
is beneficial but is not the primary objective.
