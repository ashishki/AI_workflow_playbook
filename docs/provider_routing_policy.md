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

## Routing Maturity Ladder

Do not jump directly to dynamic routing. Advance only when the lower level is
implemented or explicitly rejected with evidence.

| Level | Name | Requirement |
|-------|------|-------------|
| L0 | No LLM | Deterministic script, CI, schema validation, or rules solve the workload |
| L1 | Static role-based model selection | Reviewer / implementer / summarizer / verifier model classes declared |
| L2 | Effort and output control | Max tokens, reasoning/effort caps, structured output, final-answer-only where applicable |
| L3 | Cache-aware execution | Stable prefix, volatile suffix, cache hit telemetry, session pinning where useful |
| L4 | Async/batch lane | Evals, enrichment, reports, or nightly checks moved to lower-cost async/batch execution |
| L5 | Evaluated dynamic routing | Router has eval set, quality floor, latency SLO, cache-hit guard, stale-router policy |
| L6 | Cascade with calibrated verifier | Cheap-first path allowed only with calibrated independent verifier and measured escalation threshold |

Default maturity target:

- Lean: L0-L2 unless a specific AI workload justifies more
- Standard: L1-L4 for recurring AI usage
- Strict: L1-L4 baseline; L5/L6 only with `docs/router_eval.md`

## Routing Record

```yaml
type: provider_routing
task_id: T-123
maturity_level: L1 | L2 | L3 | L4 | L5 | L6
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
router_eval:
  required: false
  path: docs/router_eval.md
```

## Dynamic Router Gate

Dynamic routing requires `docs/router_eval.md` before production or recurring
use. The eval must show:

- quality floor is met
- cost reduction target is met
- p95 latency target is met
- cache-hit rate does not regress beyond the declared threshold
- escalation rate is within budget
- unsupported languages/domains are excluded or separately evaluated
- stale-router policy is declared

Any new model, pricing change, prompt/cache layout change, traffic mix change,
or eval regression requires re-evaluation.

## Cascade Gate

A cascade is allowed only when:

- the verifier/escalation judge is independent from the cheap model, or the
  cheap model's confidence is calibrated on the project eval set
- the escalation threshold is selected from a measured cost/quality curve
- failed cheap attempts and verifier calls are included in total cost
- false-negative rate is acceptable for the workload risk

Cheap model self-confidence is not treated as calibrated evidence. Recent
research on instruction-tuned/chat LLMs reports overconfidence in their own
responses, so self-judgment must be evaluated before it can gate escalation.
Source: https://arxiv.org/abs/2606.03437

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
- maturity level used
- router eval result when L5/L6 is active
