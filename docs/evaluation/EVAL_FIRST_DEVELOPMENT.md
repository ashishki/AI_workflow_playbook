# Evaluation-First Development

## Purpose

Evaluation is part of design, not a post-launch activity. Any project that uses
LLMs, retrieval, tool calls, agent loops, routing, or judges must define how it
will prove quality before implementation starts.

This document connects the playbook's problem-first gate to the evidence loop:

```text
project brief -> architecture -> eval dataset -> thresholds -> implementation
-> eval run -> review -> cost/SLA rollup -> runtime evidence
```

## Required Decisions

Record these decisions in Phase 1 before building AI behavior:

| Decision | Required evidence |
|----------|-------------------|
| First proof metric | One measurable signal tied to the real workflow pain |
| Evaluation dataset source | Human-labeled sample, production replay, synthetic seed set, or manual fixture |
| Quality threshold | Minimum acceptable score and regression threshold |
| Failure taxonomy | Expected failure classes and stop-ship failures |
| Human review budget | Who reviews, sample size, minutes per item, escalation path |
| Cost boundary | Inference, judge, eval generation, and human-review cost ceiling |
| Latency/SLA boundary | p50/p95/p99 target for user-facing or routine paths |
| Release gate | Advisory, blocking, or manual approval only |

## Evaluator Hierarchy

Prefer the cheapest reliable evaluator for each claim:

| Level | Use for | Gate type |
|-------|---------|-----------|
| Deterministic validators | Schema, policy, citations, exact fields, no-answer path, trace completeness | Blocking when exact |
| Golden tests | Stable task slices with known expected outputs | Blocking after baseline |
| Human labels | Ambiguous quality, domain judgment, high-risk failures | Blocking for launch approval |
| Calibrated LLM judge | Scalable scoring after agreement against human labels | Advisory until calibrated; blocking only when protocol allows |
| Production telemetry | Drift, latency, cost, retry, human override rate | Runtime gate or rollback signal |

LLM judges must not be treated as objective authority without
`docs/evaluation/JUDGE_CALIBRATION_PROTOCOL.md` or an equivalent project
artifact.

## Phase 1 Minimum

For Lean projects:

- Name the first proof metric.
- Declare a manual or automated verification command.
- Record the AI/model budget boundary if AI is used.

For Standard projects:

- Create capability eval artifacts for every active capability profile.
- Define baseline dataset, thresholds, cost boundary, and owner.
- Keep evaluation history append-only.

For Strict projects:

- Add human-review sampling.
- Calibrate any LLM judge before it can block or approve release.
- Add CI or release gates for seeded regressions and stop-ship failures.

## Regression Rule

A quality regression is not offset by lower cost unless the architecture
explicitly accepts that trade-off. Record the decision in the eval artifact and
the cost architecture. A cheaper route that increases rework, false approvals,
or operator override rate is not a real saving.

## Artifact Map

| Need | Artifact |
|------|----------|
| Project-level proof plan | `templates/PROJECT_BRIEF.md` and `templates/ARCHITECTURE.md` |
| Capability eval | `templates/RETRIEVAL_EVAL.md`, `docs/*_eval.md`, or profile-specific artifact |
| Judge calibration | `templates/JUDGE_CALIBRATION_PROTOCOL.md` |
| Harness comparison | `templates/HARNESS_BENCHMARK_CARD.md` |
| RAG data readiness | `templates/RAG_DATA_READINESS.md` |
| Cost budget | `templates/COST_BUDGET.md` and `docs/evaluation/EVAL_COST_BUDGET.md` |
| CI gate | `docs/evaluation/CI_EVAL_GATE.md` |

