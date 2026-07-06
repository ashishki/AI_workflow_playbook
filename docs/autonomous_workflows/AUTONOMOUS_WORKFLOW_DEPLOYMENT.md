# Autonomous Workflow Deployment

## Purpose

This module turns a manual or AI-assisted workflow into a bounded routine only
when the trigger, runtime, secrets, idempotency, retry, fallback, monitoring,
and budget are explicit.

It is not a mandate to build autonomous swarms.

## Deployment Decision

| Shape | Use when |
|-------|----------|
| Manual assistant | Human triggers each run and owns final action |
| Scheduled routine | Low-risk recurring task with stable inputs |
| Webhook routine | External event starts a bounded job |
| Event-driven worker | Queue/event stream requires durable handling |
| Self-hosted worker | Local data, custom runtime, or special toolchain required |
| Cloud function | Short stateless action with simple secret boundary |

## Required Contract

Every routine declares:

- trigger type
- input schema
- idempotency key
- runtime tier
- secrets source
- retry policy
- timeout
- cancellation behavior
- fallback
- monitoring
- cost budget
- human handoff trigger

Use `docs/autonomous_workflows/TRIGGER_CONTRACT.md` and
`templates/AUTONOMOUS_WORKFLOW_DEPLOYMENT.md`.

