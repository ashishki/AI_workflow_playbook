# Cost Budget

Mode: Lean | Standard | Strict
Owner:
Last updated:

## Budget Scope

| Scope | Limit | Window | Enforcement |
|-------|-------|--------|-------------|
| Per task / run | | | warn / block / approval |
| Per user / operator | | | warn / block / approval |
| Per project / month | | | warn / block / approval |
| Per agent / workflow | | | warn / block / approval |

## Attribution Tags

Every LLM call or agent run should be attributable to:

- project
- task or workflow
- agent/role
- model
- user/operator or service account
- feature/workload
- environment

## Model Routing Budget

| Workload | Default model/class | Escalation allowed when | Cheaper fallback | Verification metric |
|----------|---------------------|--------------------------|------------------|---------------------|
| | | | | |

## Cost Equation

Optimize cost per successful task, not cost per model call.

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

| Component | Measurement Source | Included? | Notes |
|-----------|--------------------|-----------|-------|
| fresh_input_cost | telemetry/provider/gateway | yes/no | |
| cached_input_cost | telemetry/provider/gateway | yes/no | |
| output_cost | telemetry/provider/gateway | yes/no | |
| tool_cost | traces/manual estimate | yes/no | |
| retry_cost | telemetry/rollup | yes/no | |
| verifier_cost | telemetry/rollup | yes/no | |
| human_rework_cost_estimate | review/ops estimate | yes/no | |
| successful_completion_rate | eval/review outcome | yes/no | |

## Guardrails

- Max model calls per run:
- Max tool calls per run:
- Max retries per failing call:
- Max parallel agents:
- Max output tokens per workload:
- Max reasoning/effort level per workload:
- Target cache hit rate:
- Max escalation rate:
- Stop condition for repeated equivalent failures:
- Human approval threshold:

## Required Measurements

- input tokens
- output tokens
- total tokens
- estimated cost
- latency
- retry count
- tool call count
- result quality/eval outcome where available

## Telemetry

- Telemetry file: `docs/ai_cost_telemetry.jsonl`
- Entry schema: `schemas/cost_telemetry_entry.schema.json`
- Rollup command:

```bash
python3 tools/cost_rollup.py \
  --input docs/ai_cost_telemetry.jsonl \
  --output reports/ai_cost_rollup.md \
  --strict
```

- CI threshold command:

```bash
python3 tools/cost_rollup.py --strict --require-file --max-total-cost {{MAX_TOTAL_COST_USD}} --max-run-cost {{MAX_RUN_COST_USD}}
```

## Review Rule

A cost-saving change is acceptable only when quality and latency stay within the
declared thresholds. A cheaper route that causes retries, rework, or lower pass
rate is not a real saving.
