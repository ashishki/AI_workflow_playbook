# Agent Harness Design

## Purpose

An agent is not only a model. It is the complete harness around the model:
prompt, tools, memory, permissions, retries, recovery, termination, traces,
cost controls, and human handoff.

This playbook treats the harness as an architecture and evaluation contract,
not as a runtime framework.

## Harness Boundary

Every Tool-Use or Agentic project should define:

| Boundary | Required decision |
|----------|-------------------|
| Model | Approved model classes, fallback, escalation rule |
| Prompt | Stable policy, task prompt, output schema, cache boundary |
| Tools | Registry, schemas, side effects, idempotency, permission class |
| Memory/state | What persists, owner, schema, retention, reset behavior |
| Loop | Max iterations, timeout, termination, partial-result behavior |
| Retry/recovery | Retry caps, retryable errors, fallback, dead-letter behavior |
| Permissions | Allowed, ask, sandbox, escalate, blocked classes |
| Trace | Required span fields, artifacts, cost, latency, decision records |
| Human handoff | When the agent must stop, ask, or request approval |
| Eval | Dataset slices, thresholds, trace completeness, cost per success |

## Non-Goals

- Do not turn the playbook into a scheduler.
- Do not add uncontrolled self-improvement.
- Do not let the model silently expand its own permissions.
- Do not compare model A vs model B without holding harness configuration
  visible and versioned.

## Required Artifact

Use `templates/AGENT_HARNESS_DESIGN.md` for project-specific harness cards.
Use `templates/HARNESS_BENCHMARK_CARD.md` when comparing baseline and candidate
harnesses.

