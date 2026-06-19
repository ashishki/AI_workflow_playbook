# AI Cost Architecture

## Purpose

AI cost is not only a budget line. It is an architecture constraint that shapes
workload classes, model tiers, prompt/cache layout, batch lanes, output caps,
retry/fan-out limits, router maturity, and escalation rules.

Use this document when a project has recurring AI/model usage, agent loops,
dynamic workflows, multi-agent review, enforceable cost thresholds, or material
inference spend.

Lean projects may keep this inline in `docs/CODEX_PROMPT.md`,
`AGENTS.md`, or `docs/CONTRACT_LITE.md`. Standard/Strict projects should create
`docs/ai_cost_architecture.md` from `templates/COST_ARCHITECTURE.md` when cost
is material or recurring.

## Architecture Boundary

Model routing is a policy execution detail inside architecture boundaries.
Architecture decides:

- workload classes and role boundaries
- model tiers allowed for each workload
- budget limits and approval thresholds
- cache layout and cache-hit targets
- output-token, effort, retry, and fan-out caps
- batch/async lanes
- eval floors and stale-router policy
- cascade and escalation rules

A router may choose only within those declared boundaries. If the router changes
quality, risk, data exposure, budget, or human approval boundaries, that is an
architecture change and requires an ADR or equivalent decision record.

## Required Sections

### Workload Classes

Each AI-owned workload needs an explicit class:

```yaml
workload_classes:
  - name: architecture_review
    default_model_class: frontier
    fallback_allowed: false
    cache_required: true
    max_output_tokens: 2500
    max_cost_usd_per_run: 5
    quality_floor: "no unresolved P0/P1 review miss on eval set"

  - name: implementation_fix
    default_model_class: implementation_grade
    fallback_allowed: true
    max_correction_turns: 2
    max_output_tokens: 1800
    max_cost_usd_per_task: 3

  - name: summarization_packet
    default_model_class: low_cost
    deterministic_preferred: true
    batch_allowed: true
    max_output_tokens: 900
```

### Cost Levers

Declare which levers are active:

```yaml
cost_levers:
  prompt_cache: required_for_long_context
  batch_api: required_for_async_bulk
  output_caps: required
  reasoning_effort_caps: required_when_available
  model_escalation: approval_required
  dynamic_router: eval_required
  cascades: calibrated_verifier_required
```

### Cache Context Layout

If prompt caching is used, the project must declare stable-prefix and
volatile-suffix boundaries. See `docs/cache_context_layout.md`.

### Batch / Async Lane

Batch lanes are for evals, enrichment, reports, nightly checks, or other
latency-insensitive work. They should not be used for interactive or
human-blocking work unless the product explicitly accepts delayed results.

### Routing Maturity

Use the routing maturity ladder in `docs/provider_routing_policy.md`. Do not
start with dynamic routing. Prefer deterministic code, static role-based model
selection, output/effort caps, cache-aware execution, and batch lanes before
allowing evaluated dynamic routing.

### Cascades

A cascade is allowed only if:

- the escalation judge is not the same cheap model, or
- the cheap model confidence is calibrated on the project eval set
- the escalation threshold is chosen from a measured cost/quality curve
- failed cheap attempts are included in `cost_per_successful_task`
- the verifier's false-negative rate is acceptable for the workload risk

Do not let a cheap model self-certify high-risk outputs. Recent calibration
research reports that instruction-tuned/chat LLMs can be overconfident in their
own responses; treat self-reported confidence as untrusted unless calibrated.
Source: https://arxiv.org/abs/2606.03437

## Required Evidence

Cost architecture is enforceable only when connected to artifacts:

- `docs/COST_BUDGET.md` for budget limits
- `docs/ai_cost_telemetry.jsonl` or an equivalent telemetry source
- `reports/ai_cost_rollup.md` for actual rollups
- `docs/router_eval.md` when dynamic routing or cascades are used
- capability eval artifacts when routing affects RAG/tool/agent/planning outputs

## Review Questions

- Does every AI workload have a declared model class and output cap?
- Are cacheable prompts structured with stable prefixes and volatile suffixes?
- Are model escalation and router changes approval-gated?
- Does cost telemetry measure cost per successful task, not only cost per call?
- Does any dynamic router have an eval set, stale-router policy, and quality
  floor?
- Does any cascade include failed cheap attempts and verifier cost in the total?
