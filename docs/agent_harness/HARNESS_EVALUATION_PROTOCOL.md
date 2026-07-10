# Harness Evaluation Protocol

Status: authoritative

## Purpose

The evaluated unit is not a base model. It is:

`model + prompt + tools + memory/state + permissions + retries + recovery + trace + scorer + environment`

This protocol is an architecture and evaluation contract. The core Playbook
remains a governance control plane; runnable experiments live in the isolated
companion package at `companion/ai_workflow_harness_lab/`.

## Boundary

Every Tool-Use or Agentic project should make these boundaries explicit:

| Boundary | Required decision |
|----------|-------------------|
| Model | Approved model class, exact model ID for runs, fallback, escalation |
| Prompt | Stable policy, task prompt, output schema, cache boundary |
| Tools | Registry, schemas, side effects, idempotency, permission class |
| Memory/state | What persists, owner, schema, retention, reset behavior |
| Loop | Max iterations, timeout, termination, partial-result behavior |
| Retry/recovery | Retry caps, retryable errors, fallback, dead-letter behavior |
| Permissions | Allowed, ask, sandbox, escalate, blocked classes |
| Trace | Required span fields, artifacts, cost, latency, decision records |
| Human handoff | When the agent must stop, ask, or request approval |
| Eval | Dataset slices, thresholds, trace completeness, cost per success |

## Versioned Contracts

- `schemas/harness_eval_unit.schema.json`
- `schemas/command_receipt.schema.json`
- `schemas/failure_record.schema.json`
- `schemas/run_result.schema.json`
- `schemas/evidence_bundle.schema.json`

## Required Slices

| Slice | Checks |
|-------|--------|
| Happy path | Completes task under normal conditions |
| Ambiguous input | Asks for missing information instead of guessing |
| Tool error | Recovers, retries within cap, or escalates |
| Permission boundary | Stops before unsafe/destructive action |
| Long loop | Terminates at max iterations or timeout |
| Evidence-grounded | Uses observed state, citations, or tool outputs correctly |
| Cost pressure | Stays within model/tool/retry budget |
| Trace completeness | Run can be reconstructed from logs and artifacts |

## Metrics

Do not collapse safety, false completion, task quality, infrastructure validity,
cost, latency, and human intervention into one aggregate score.

Required metrics include:

- task success rate
- verified environment success rate
- false-success rate
- regression rate
- recovery success rate
- policy violation rate
- evidence completeness
- evidence correctness
- tool-call count
- unnecessary action count
- retry count
- timeout rate
- invalid infrastructure run rate
- input/output tokens when telemetry exists, otherwise `unknown`
- wall-clock latency
- cost per attempted task
- cost per successful task
- human intervention rate
- cross-session continuity success

Safety, false completion, and immutable-policy violations are hard gates.

## Evidence Rule

An agent may produce output and trace, but it must not assign final `passed`,
`verified`, `accepted`, or `release_ready` status. Final verdicts come from:

- `tools/validate_harness_evidence.py`
- independent scorers
- a separate human-review receipt when human judgment is required

## Companion Implementation

The minimal runnable evaluation mechanism is implemented in:

`companion/ai_workflow_harness_lab/`

The companion package:

- consumes Playbook schemas and task files;
- materializes a fresh workspace for every trial;
- runs scripted or command adapters;
- executes independent scorers after the adapter;
- writes EvidenceBundles;
- compares baseline and candidate conditions from raw bundles.

It is intentionally not a database, Web UI, Docker platform, provider gateway,
or required dependency for ordinary Playbook adoption.
