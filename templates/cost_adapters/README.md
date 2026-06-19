# Cost Adapter Templates

These templates give downstream projects a concrete provider boundary for
writing `docs/ai_cost_telemetry.jsonl`.

They are intentionally provider-neutral. They do not monkey-patch SDKs. Each
project should route OpenAI, Anthropic, gateway, agent-runtime, or local model
calls through one owned module and call the adapter after each provider call.

Use when:

- `docs/COST_BUDGET.md` declares enforceable thresholds
- `docs/ai_cost_architecture.md` declares workload classes, cache targets,
  routing maturity, or cascade policy
- the project needs CI cost rollups from `tools/cost_rollup.py`

Do not use as-is for regulated billing. Pricing and usage accounting must be
validated against the provider or gateway source of truth.
