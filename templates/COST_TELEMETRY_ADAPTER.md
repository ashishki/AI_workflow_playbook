# Cost Telemetry Adapter

Use this template inside a downstream project when `docs/COST_BUDGET.md`
declares enforceable AI/model cost thresholds.

## Build Pattern

All provider calls must pass through one project-owned boundary:

```text
app/ai/client.py
app/ai/telemetry.py
```

or the equivalent path for the project's stack.

Do not scatter direct OpenAI, Anthropic, gateway, or agent SDK calls throughout
application code. If a provider call bypasses this boundary, cost attribution
and budget gates are incomplete.

## Required Adapter Responsibilities

The adapter must:

- call the provider/gateway/SDK
- extract provider-returned usage when available
- compute or receive `estimated_cost_usd`
- attach attribution fields: project, task/workflow, run_id, agent_role, model,
  operator/user, feature, workload_class, routing_maturity_level, environment
- attach cache/routing fields when applicable: cache_hit, cache_read_tokens,
  cache_write_tokens, router_decision, escalation_reason
- append one entry to `docs/ai_cost_telemetry.jsonl` in local/test workflows or
  export the same JSON shape to the selected gateway/observability backend
- expose a test seam using a fake provider response
- fail or request approval when a run would exceed the declared budget

## Required Test Shape

Add tests that prove:

- a fake provider response with usage writes one valid JSONL entry
- missing usage is recorded as `source: manual_estimate` or is rejected,
  depending on the project policy
- `total_tokens` matches `input_tokens + output_tokens`
- cache/routing fields are present when `docs/ai_cost_architecture.md`
  declares prompt caching, dynamic routing, or cascades
- `tools/cost_rollup.py --strict --require-file` passes on the generated
  telemetry fixture
- a configured `--max-run-cost` threshold fails when exceeded

## Task Skeleton

```markdown
## T{{NN}}: AI Cost Telemetry Adapter

Owner:      codex
Phase:      {{phase}}
Type:       cost:telemetry
Depends-On: {{provider client task or none}}

Objective: |
  Route all LLM/provider calls through a project-owned telemetry adapter that
  records usage and estimated cost in the playbook telemetry format.

Acceptance-Criteria:
  - id: AC-1
    description: "A fake provider response with usage writes one JSONL entry matching schemas/cost_telemetry_entry.schema.json."
    test: "{{test path}}::test_writes_cost_telemetry_entry"
  - id: AC-2
    description: "The cost rollup command passes against the generated telemetry fixture."
    test: "python3 tools/cost_rollup.py --input {{fixture path}} --output reports/ai_cost_rollup.md --strict --require-file"
  - id: AC-3
    description: "The adapter blocks or requests approval when max-run-cost is exceeded."
    test: "{{test path}}::test_budget_threshold_requires_approval"

Files:
  - {{app ai client path}}
  - {{app ai telemetry path}}
  - {{test path}}
  - docs/COST_BUDGET.md
```
