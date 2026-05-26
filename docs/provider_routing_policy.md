# Provider Routing Policy

## Purpose

Support multi-model and multi-provider workflows without hiding model
differences behind a generic router.

## Default Posture

Role-based model selection remains the default:

- architecture/review: architecture-grade model
- implementation/fixes/tests: implementation-grade model
- summarization or packet generation: low-cost model or deterministic script
- verification: deterministic script or CI whenever possible

Provider fallback is optional. It must be explicit for tasks where model
identity affects correctness, safety, or auditability.

## Routing Record

```yaml
type: provider_routing
task_id: T-123
role: implementer
primary_provider: codex
fallback_allowed: true
fallback_providers:
  - openai
  - anthropic
budget:
  max_turns: 5
  max_cost_usd: 10
circuit_breakers:
  rate_limit_cooldown_seconds: 300
  repeated_failure_threshold: 2
degraded_mode:
  allowed: true
  behavior: "finish analysis, do not write files"
```

## Fallback Rules

- Fallback is allowed for transient provider failures, rate limits, and
  non-architecture routine implementation.
- Fallback is not automatic for architectural decisions, security-sensitive
  reviews, compliance judgments, or phase gates.
- Fallback must preserve role boundaries. A provider change must not turn a
  reviewer into an implementer or an implementer into its own reviewer.
- Degraded mode should prefer analysis-only output over unverified writes.

## Circuit Breakers

Open a circuit breaker when:

- provider returns repeated rate-limit or overload errors
- provider returns incomplete streamed output
- latency exceeds the task's timeout repeatedly
- output repeatedly fails schema or verification checks

When open, route away for a fixed cooldown or require human approval for
continued use.

## Budget Handling

- Track turns and estimated cost per session.
- Warn at 80% of budget.
- Stop at 100% with a resumable state update.
- Do not disable budgets for autonomous correction loops.

## Review Check

Provider routing is successful only when the result records:

- provider/model actually used
- fallback reason, if any
- whether fallback changed task risk
- budget consumed
- verification outcome
