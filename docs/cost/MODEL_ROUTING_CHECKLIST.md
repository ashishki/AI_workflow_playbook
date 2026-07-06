# Model Routing Checklist

## Checklist

| Check | Required evidence |
|-------|-------------------|
| Workload classes declared | `docs/ai_cost_architecture.md` |
| Approved model classes per workload | Architecture or cost artifact |
| Escalation rules | Quality, confidence, risk, or budget trigger |
| Quality floor | Eval threshold per route |
| Cost target | Budget and telemetry |
| Latency target | SLA artifact |
| Cache impact | Stable-prefix and cache-hit plan |
| Failure handling | Fallback, retry, or human handoff |
| Stale-router policy | Re-eval trigger and owner |
| Cascade verifier calibrated | Judge calibration or deterministic verifier |

## Anti-Patterns

- dynamic routing without `docs/router_eval.md`
- cheap model self-certifies high-risk output
- route chosen only by token price
- routing change without latency and cache-hit evidence
- escalation path with no budget approval trigger

