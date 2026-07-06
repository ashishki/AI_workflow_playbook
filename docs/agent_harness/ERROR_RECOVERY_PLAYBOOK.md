# Error Recovery Playbook

## Purpose

Agentic systems need explicit recovery rules. A retry loop is not a recovery
strategy.

## Error Classes

| Error class | Default behavior |
|-------------|------------------|
| Invalid input | Ask user or return validation error |
| Missing prerequisite | Stop and request the missing artifact or approval |
| Tool schema error | Do not execute; request corrected structured call |
| Tool transient failure | Retry only if idempotent and under cap |
| Tool permanent failure | Fallback or human handoff |
| Permission denied | Stop; do not route around the boundary |
| Insufficient evidence | Return `insufficient_evidence` or ask for source |
| Budget exceeded | Stop or request approval |
| Max iterations reached | Return partial result with trace and unresolved items |
| Unsafe output | Block output and create review finding |

## Recovery Contract

Every recovery rule should define:

- detection condition
- retry cap
- idempotency requirement
- fallback action
- human handoff condition
- trace event
- eval case

## No Silent Workaround Rule

If the agent lacks permission, data, credentials, context, or approval, it must
ask or stop. It must not fabricate substitute evidence, bypass a tool, downgrade
security, or claim completion with missing proof.

