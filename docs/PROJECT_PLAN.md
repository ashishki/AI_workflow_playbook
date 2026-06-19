# AI Workflow Playbook - Project Plan

Status: active core framework
Role: operating system for AI-assisted engineering
Priority: P0

## Strategic Role

AI Workflow Playbook remains the canonical governance layer for the portfolio. It
defines how projects are planned, implemented, reviewed, verified, documented,
and resumed across agents and machines.

The playbook is not a product UI and should not become a mandatory runtime. Its
value is protocol discipline: contracts, evidence, review, phase gates, runtime
verification, and cognition integrity.

## Near-Term Roadmap

### P0 - Consolidate Zero-Trust Execution

- Integrate Runtime Verification Protocol into default task templates.
- Add README-first knowledge index as a phase-gate navigation artifact.
- Keep AI/model cost guardrails first-class in bootstrap, validator,
  orchestrator, and review prompts.
- Keep AI cost architecture first-class where spend is recurring/material or
  uses prompt caching, batch lanes, dynamic routing, or cascades.
- Treat external agent skills as supply-chain artifacts with trust records,
  scan/provenance/signature evidence, and explicit install scope before they
  enter project or global agent context.
- Add examples of `runtime_verification`, `decision_receipt`, and
  `risk_acceptance_record`.
- Add CI example for `tools/integrity_check.py`.
- Add reviewer checklist rows for stale cognition packets and broken
  Context-Refs.

### P1 - Add Entropy-Inspired Evidence Layer

- Define playbook-native receipt schemas:
  - `agent_action_receipt`
  - `decision_receipt`
  - `referee_review_record`
  - `risk_acceptance_record`
- Keep receipts as artifacts, not infrastructure dependencies.
- Use `docs/entropy_core_and_gensyn_reference_policy.md` to keep Entropy Core
  references optional and Gensyn-inspired patterns bounded.
- Add examples for implementation, review, provider fallback, and eval
  regression.

### P1 - Add Diverse Review Principle

- Document that role/model diversity is useful for high-risk work because
  different reviewers find different failure niches.
- Do not add swarm behavior.
- Keep consolidation human-readable and evidence-backed.

### P2 - Portfolio Integration

- Add a portfolio operating guide showing how Playbook, Entropy Core, Workflow
  Studio, Training OS, Radar, and Telegram Intelligence fit together.
- Keep migration/adoption modes current for projects that only need the Lean
  path (`docs/adoption_modes.md`, `docs/usage_guide.md`).

### Completed Baseline Decisions

- Lean / Standard / Strict are real adoption modes, not softer wording for the
  same full artifact set.
- External runtimes and dynamic workflows are reference patterns, not mandatory
  playbook dependencies.
- AI/model budget boundaries are mandatory for active AI work. Dedicated
  `docs/COST_BUDGET.md` is required for recurring, multi-agent,
  dynamic-workflow, multi-user, or materially costly AI usage in Standard/Strict
  projects.
- AI cost architecture is now separate from budget policy. Standard/Strict
  projects use `docs/ai_cost_architecture.md` for workload classes, cache
  layout, batch lanes, routing maturity, cascades, and cost-per-successful-task
  when AI spend is recurring/material or routing/caching is part of the design.
- Dynamic routing and cascades require `docs/router_eval.md`; generic routers
  remain disallowed until evaluated against project traffic, quality floors,
  latency, cache-hit impact, and stale-router policy.
- Provider-agnostic AI cost telemetry now has a JSONL entry contract and rollup
  tool. Provider SDK auto-instrumentation remains optional v2 adapter work.
- External skill security now has a policy and trust-record template. Third-
  party or cross-project skills require source pin/signature/hash, capability
  declaration, SkillSpector or equivalent scan evidence, finding triage, install
  scope, and human approval for global install or high-risk acceptance.

## AI-Development Tasks

- Use Codex for doc/protocol edits only after task scope is explicit.
- Require runtime verification for risky prompt/template changes.
- Use reviewer agents for architecture-impacting changes.
- Do not use autonomous self-repair beyond bounded correction rules.

## Stop Conditions

- If a proposed feature requires a server, database, or UI, it likely belongs in
  another project.
- If a protocol cannot be explained as an artifact/check/workflow, do not add it.
