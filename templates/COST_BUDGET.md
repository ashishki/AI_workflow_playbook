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

## Guardrails

- Max model calls per run:
- Max tool calls per run:
- Max retries per failing call:
- Max parallel agents:
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
