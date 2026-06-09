# Cost Guardrails Research

Last verified: 2026-06-09

## Signal

The external signal is strong enough to make cost guardrails first-class in the
playbook. Recent vendor writing, product docs, research papers, and practitioner
threads converge on the same failure class: agentic systems do not only need
aggregate invoice tracking; they need per-run attribution, budgets, and stop
conditions.

## Evidence

| Source | What It Supports | URL |
|--------|------------------|-----|
| Braintrust: cost tracking playbook | Invoice-level spend is too coarse; request-level spans should carry token counts, estimated cost, user/org metadata, and quality/latency context. Cost-saving changes should be promoted only when eval pass rate and latency hold. | https://www.braintrust.dev/articles/how-to-track-llm-costs-2026 |
| Braintrust: tracking tools review | Cost analysis should connect to experiments and evals so prompt/model/workflow changes can be tested before production. | https://www.braintrust.dev/articles/best-tools-tracking-llm-costs-production-2026 |
| TrueFoundry AI Gateway budget limiting | Budget limiting can apply to users, teams, virtual accounts, applications, models, and combinations; matching rules can enforce limits before runaway spend. | https://www.truefoundry.com/docs/ai-gateway/budgetlimiting |
| TrueFoundry CI/CD token explosion | Agentic CI/CD workflows can outspend customer-facing workloads; budget/rate controls need rule order and layered tracking. | https://www.truefoundry.com/blog/the-agentic-token-explosion-in-ci-cd |
| Maxim agent observability | Agent traces should include sessions, spans, LLM calls, tool calls, retrieval, token usage, latency, cost per request, quality scores, and alerts. | https://www.getmaxim.ai/products/agent-observability |
| Maxim token/cost docs | Cost tracking needs provider usage objects or explicit token/cost fields, plus custom pricing where provider/default pricing is insufficient. | https://www.getmaxim.ai/docs/observe/how-to/log-your-application/track-token-usage-and-cost |
| OpenAI Agents SDK usage docs | Agents SDK tracks token usage per run and per request, enabling cost monitoring and context-window monitoring. | https://openai.github.io/openai-agents-python/usage/ |
| OpenAI API rate and usage limits | Provider-level rate/usage limits exist, but they are organization/project-level and should not replace per-user/workflow application budgets. | https://developers.openai.com/api/docs/guides/rate-limits#usage-tiers |
| Claude Agent SDK cost docs | Claude SDK exposes per-step and per-model usage/cost; parallel tool calls must be deduplicated by message ID to avoid double-counting. | https://code.claude.com/docs/en/agent-sdk/cost-tracking |
| Arxiv: Token Budgets, 2026 | Budget overruns are a documented production failure class; retry loops and delegation fan-out need non-bypassable budget controls. | https://arxiv.org/abs/2606.04056 |
| Arxiv: coding-agent token consumption, 2026 | Agentic coding tasks can consume far more tokens than code chat/reasoning; token use is highly variable and higher spend does not guarantee higher accuracy. | https://arxiv.org/abs/2604.22750 |
| Reddit practitioner threads | Practitioners ask for per-agent, per-task, per-customer cost tracking, hard caps, alerts, and approval before expensive operations. Treat as weak evidence but useful demand signal. | https://www.reddit.com/r/AI_Agents/comments/1rgfe7f/how_are_you_tracking_cost_per_agent_in_production/ |

## Implications For The Playbook

- Cost must be declared during project brief and architecture, not discovered
  after implementation.
- `docs/COST_BUDGET.md` should exist for recurring AI usage, agent loops,
  dynamic workflows, multi-user systems, and Strict projects.
- Orchestrator and reviewer prompts should flag model escalation, unbounded
  retries, missing budgets, and fan-out without caps.
- Cost optimization must be evaluated against quality and latency; cheaper calls
  are not cheaper if they increase retries or rework.
- Per-run attribution is more useful than monthly totals for debugging agentic
  waste.

## Recommended Minimum

Lean:

- budget note in `docs/CODEX_PROMPT.md` or contract-lite
- per-task budget
- deterministic review for low-risk work
- stop on projected overrun

Standard:

- `docs/COST_BUDGET.md`
- per-run, per-agent, per-feature attribution
- model routing table
- `tools/cost_rollup.py` rollup when telemetry data exists
- reviewer check for cost drift

Strict:

- hard budget gates
- CI cost telemetry threshold when telemetry data exists
- approval before overrun
- max calls / retries / fan-out
- cost summary at phase gate
- evidence that cost-saving changes preserved quality and latency

## Anti-Patterns

- tracking only monthly invoices
- relying only on provider-level project limits for multi-tenant products
- letting agents self-escalate to stronger models
- unbounded retry loops
- unbounded parallel agents
- treating eval, latency, and cost as separate decisions
- adopting observability tooling without enforcement thresholds
