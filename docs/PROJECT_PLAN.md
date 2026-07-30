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

### P0 - Keep The Core Workflow Legible

- Keep `docs/README.md`, `docs/EVIDENCE_INDEX.md`, and `reports/README.md`
  current so agents can distinguish authority, optional references, and
  historical evidence without broad-loading the repository.
- Keep the current Codex Direct path and Feature Workflow path synchronized
  across `README.md`, `PLAYBOOK.md`, `docs/usage_guide.md`,
  `docs/adoption_modes.md`, and `tools/README.md`.
- Remove or archive root-level research dumps, stale reports, and compatibility
  wrappers only after their current authority is mapped.
- Do not add placeholder artifacts only to satisfy a checklist.

### P1 - Complete Remaining Mechanism Work

- Implement the real sequential changeability runner described by
  `AWP-PI-010` once the Feature Workflow lifecycle remains green.
- Add examples of `runtime_verification`, `decision_receipt`, and
  `risk_acceptance_record` only where they have an executable consumer or clear
  downstream task.
- Add a CI example for `tools/integrity_check.py`.
- Keep reviewer checklist rows for stale cognition packets and broken
  Context-Refs aligned with validators.

### P2 - Portfolio And Optional Extensions

- Add a portfolio operating guide only if it names actual source-of-truth repos
  and does not turn the Playbook into a control plane for unrelated products.
- Keep Entropy/Hermes/Mythos/dynamic workflow references optional and bounded.
- Consider optional second-model reviewer guidance for high-risk work, without
  making multi-model review a default requirement.

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
- Provider-agnostic AI cost telemetry now has a JSONL entry contract, rollup
  tool, and provider-neutral starter adapter template. Provider-specific SDK
  wrappers remain optional downstream work when the runtime/provider layer is
  known.
- External skill security now has a policy and trust-record template. Third-
  party or cross-project skills require source pin/signature/hash, capability
  declaration, SkillSpector or equivalent scan evidence, finding triage, install
  scope, and human approval for global install or high-risk acceptance.
- `tools/init_playbook_project.py` now creates a proportional Lean / Standard /
  Strict starter kit without overwriting existing downstream files by default.
- `tools/skill_security_gate.py` now provides a CI-friendly trust-record and
  SkillSpector wrapper for external skills.
- RAG Evaluation v2 now has offline deterministic contracts, scoring,
  comparison, initializer integration, and a runnable mechanism example.
- Test-first governance now has task metadata, holdout/property/UI protocols,
  critic prompts, and pilot evidence. The first paired pilot did not support a
  quality or productivity improvement claim.
- Planning Depth, Feature Design, vertical slices, hash-bound human approval,
  and the thin `tools/feature_workflow.py` lifecycle are now implemented as
  proportional pre-implementation design controls.

## AI-Development Tasks

- Use Codex for doc/protocol edits only after task scope is explicit.
- Require runtime verification for risky prompt/template changes.
- Use reviewer agents for architecture-impacting changes.
- Do not use autonomous self-repair beyond bounded correction rules.

## Stop Conditions

- If a proposed feature requires a server, database, or UI, it likely belongs in
  another project.
- If a protocol cannot be explained as an artifact/check/workflow, do not add it.
