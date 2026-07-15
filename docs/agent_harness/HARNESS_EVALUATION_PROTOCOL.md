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

- `schemas/harness_eval_unit.schema.json` (emitted by `harness-lab run` as
  `harness_eval_unit.json`)
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

For command adapters, the process exit code is part of the evidence. Non-zero
adapter exits, missing commands, timeouts, scorer exceptions, and invalid bundle
references create failure records and can fail the CLI with
`--fail-on-invalid-run`. If a task requires a verification command, the harness
runs it after the adapter and records a separate receipt; an agent's own prose
claim is not treated as proof that tests passed.

## Companion Implementation

The minimal runnable evaluation mechanism is implemented in:

`companion/ai_workflow_harness_lab/`

The companion package:

- consumes Playbook schemas and task files;
- materializes a fresh workspace for every trial;
- runs scripted or command adapters;
- propagates adapter exit codes and required verification receipts;
- executes independent scorers after the adapter;
- writes EvidenceBundles;
- validates bundles before comparing baseline and candidate conditions from raw
  evidence.

It is intentionally not a database, Web UI, Docker platform, provider gateway,
or required dependency for ordinary Playbook adoption.

## Project-Specific Benchmark Rule

The bundled `playbook_core_v1` suite is a mechanism test for the Playbook
workflow. It is not proof that any particular product, repository, or domain
benefits from Playbook adoption.

Project-specific claims require a project-specific suite with representative
fixtures, baseline and Playbook-Min prompts, traps based on that project's real
failure modes, independent scorers, pass/fail rules, and expected failure
taxonomy.

Do not generate benchmark content automatically and treat it as evidence.
Scaffolding directories is acceptable; proof starts only when maintainers add
project-specific fixtures, traps, and scorers.

## Project-Specific Holdout Modeling

A project may model a required/optional holdout as a restricted suite, config,
or verifier owned by a curator and trusted runner. Public fixtures and prompts
remain implementer-visible and must not contain restricted cases or expected
outputs. Run the protected oracle after the adapter against the exact post-state,
from a trusted process outside the agent's access/context boundary. The verifier
may inspect the same target checkout, but its cases, expected outputs, config,
and raw results must not be copied into the agent-visible workspace.

The protected wrapper may produce a command receipt, scorer output, and
EvidenceBundle when those artifacts can be sanitized and stored under the
project's restricted ACL. Expose only the suite ID/version/digest, coarse
`pass | fail | invalid | flaky | contaminated` result, redaction state, and
sanitized evidence reference to the Test Critic/consolidated review.

The companion package models isolated trials, receipts, independent scoring,
and evidence validation. It is not an access-control, secrets, or holdout-storage
boundary. A project-owned CI/policy layer must interpret the protected result:
a required `fail` blocks, while an `invalid` run is not a capability failure but
still does not satisfy the gate. Follow
`docs/testing/holdout_acceptance.md` for access, contamination, rotation, and
repair rules.
