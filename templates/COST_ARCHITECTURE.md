# AI Cost Architecture

Mode: Lean | Standard | Strict
Owner:
Last updated:

## Applicability

- AI/model usage: none | one-off | recurring | agentic | dynamic workflow | multi-agent review
- Cost materiality: low | medium | high
- Architecture artifact required: yes | no
- Reason if not required:

## Inference Posture

| Option | Decision | Evidence |
|--------|----------|----------|
| API-first | selected / rejected / hybrid | workload, data boundary, SLA, eval evidence |
| Self-hosted | selected / rejected / hybrid | TCO, serving benchmark, ops owner |
| Hybrid | selected / rejected | route boundary, data boundary, fallback |

Rule: self-hosted inference requires a measurable workload, eval set, latency
target, and cost-per-successful-task comparison. Do not select it only because
raw token price appears lower.

## Workload Classes

| Workload | Default model/class | Fallback allowed | Cache required | Batch allowed | Max output tokens | Max cost per run/task | Quality floor |
|----------|---------------------|------------------|----------------|---------------|-------------------|-----------------------|---------------|
| architecture_review | | yes/no | yes/no | yes/no | | | |
| implementation_fix | | yes/no | yes/no | yes/no | | | |
| summarization_packet | | yes/no | yes/no | yes/no | | | |

## Latency Class and SLA

| Workload | Latency class | p50 target | p95 target | Timeout | Fallback |
|----------|---------------|------------|------------|---------|----------|
| | interactive / human-blocking async / background batch / scheduled routine | | | | |

## Cost Levers

| Lever | Policy | Evidence |
|-------|--------|----------|
| Prompt cache | required / optional / n/a | cache-hit telemetry or rationale |
| Batch API / async lane | required / optional / n/a | workload list |
| Output caps | required / optional / n/a | max token settings |
| Reasoning/effort caps | required / optional / n/a | model settings |
| Model escalation | approval required / automatic / forbidden | approval rule |
| Dynamic router | eval required / forbidden / n/a | `docs/router_eval.md` |
| Cascades | calibrated verifier required / forbidden / n/a | router/cascade eval |

## Eval and Human Review Cost

| Cost area | Budget | Measurement source | Included in cost_per_successful_task? |
|-----------|--------|--------------------|---------------------------------------|
| Eval inference | | | yes/no |
| Judge inference | | | yes/no |
| Human labeling/review | | | yes/no |
| Rework/correction | | | yes/no |

## Cache Context Layout

Use `docs/cache_context_layout.md`.

```yaml
stable_prefix:
  - system policy
  - role contract
  - tool schemas
  - canonical project context
cache_breakpoint:
  provider:
  location:
  ttl:
volatile_suffix:
  - current user message
  - current diff
  - latest test output
prohibited_in_prefix:
  - timestamp
  - run_id
  - random_id
  - transient diagnostics
telemetry:
  cache_hit_metric:
  target_hit_rate:
```

## Batch / Async Lane

| Workload | Batch allowed | Why latency can be delayed | Budget cap | Verification |
|----------|---------------|----------------------------|------------|--------------|
| | | | | |

## Routing Maturity

- Current level: L0 | L1 | L2 | L3 | L4 | L5 | L6
- Target level this phase:
- Dynamic routing allowed: yes | no
- If yes, evidence: `docs/router_eval.md`

## Cascade Policy

- Cascades allowed: yes | no
- Escalation judge:
- Same cheap model self-judge allowed: no unless calibrated
- Calibration/eval source:
- Escalation threshold:
- Cost/quality curve:
- Failed cheap attempt included in cost: yes | no

## Cost Equation

```text
cost_per_successful_task =
  (fresh_input_cost
 + cached_input_cost
 + output_cost
 + tool_cost
 + retry_cost
 + verifier_cost
 + human_rework_cost_estimate)
 / successful_completion_rate
```

## Artifacts

- Budget: `docs/COST_BUDGET.md`
- Telemetry: `docs/ai_cost_telemetry.jsonl` or equivalent
- Rollup: `reports/ai_cost_rollup.md`
- Router eval: `docs/router_eval.md` if L5/L6 routing is used
- Capability evals:
