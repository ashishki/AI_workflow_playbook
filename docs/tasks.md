# AI Workflow Playbook Tasks

Status: active core framework task graph
Last updated: 2026-06-09

This file tracks framework work for the playbook itself. It is separate from
project adoption tasks in downstream repositories.

## Active Direction

Preserve the playbook as a governance-first, deterministic-first, artifact-first
engineering workflow. Do not turn it into a required runtime, orchestration
server, dynamic workflow framework, or Mythos/Entropy clone.

## Phase ZT-1 - Zero-Trust Execution Consolidation

### AWP-ZT-004: README-First Knowledge Index Gate

Owner: codex
Type: docs protocol
Status: done 2026-06-08

Objective: |
  Add README-first knowledge indexes as lightweight navigation artifacts at
  phase gates, without turning README files into authority or adding a new
  memory runtime.

Acceptance-Criteria:
  - `docs/readme_first_knowledge_index.md` defines when README indexes are
    required and how they relate to canonical artifacts.
  - `templates/README_INDEX.md` provides a concise repo/folder index shape.
  - Orchestrator and reviewer prompts check README index updates at phase
    boundaries or changed subsystem boundaries.
  - Cognition/vault docs state that README indexes are local navigation and the
    vault remains cross-project convenience.

Integration-Points:
  - `docs/readme_first_knowledge_index.md`
  - `templates/README_INDEX.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/cognition/`

Evidence:
  - `docs/readme_first_knowledge_index.md`
  - `templates/README_INDEX.md`
  - `docs/usage_guide.md`
  - `docs/cognition/vault_usage_protocol.md`

### AWP-ZT-001: Runtime Verification Template Integration

Owner: codex
Type: docs template
Status: done 2026-05-29

Objective: |
  Integrate runtime verification records into the default task/review flow for
  risky writes and agent claims.

Acceptance-Criteria:
  - `templates/` includes a concise runtime verification record example.
  - Review checklists require diff/hash/test evidence for claimed risky writes.
  - Docs keep filesystem/repo state as authoritative over model claims.

Integration-Points:
  - `docs/runtime_verification_protocol.md`
  - `docs/filesystem_reality_principle.md`
  - `templates/`
  - `prompts/`

Evidence:
  - `templates/RUNTIME_VERIFICATION_RECORD.md`
  - `templates/tasks_schema.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

### AWP-ZT-002: Agent Claim Verification Checklist

Owner: codex
Type: docs review
Status: done 2026-05-29

Objective: |
  Add explicit reviewer checks for claimed files, claimed tests, claimed
  decisions, and claimed context references.

Acceptance-Criteria:
  - Review prompts ask for evidence behind every material completion claim.
  - Claimed files must exist; claimed tests must have command evidence.
  - Claimed decisions must link to ADRs, decision logs, or review records.

Integration-Points:
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`
  - `docs/integrity_verification_jobs.md`

Evidence:
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

### AWP-ZT-003: Bounded Correction Defaults

Owner: codex
Type: docs protocol
Status: done 2026-05-29

Objective: |
  Make bounded correction turns the default for self-repair loops.

Acceptance-Criteria:
  - Task/review docs state the retry limit and escalation rule.
  - Intermediate state must be preserved when retries fail.
  - Autonomous repair loops cannot continue without human decision after the
    configured bound.

Integration-Points:
  - `docs/bounded_correction_turns.md`
  - `PLAYBOOK.md`
  - `prompts/`

Evidence:
  - `docs/bounded_correction_turns.md`
  - `templates/CODEX_PROMPT.md`
  - `templates/tasks_schema.md`
  - `prompts/ORCHESTRATOR.md`

## Phase EL-1 - Evidence Layer

### AWP-EL-001: Playbook-Native Receipt Schemas

Owner: codex
Type: docs protocol
Status: planned

Objective: |
  Define portable receipt examples for agent actions, decisions, referee reviews,
  and risk acceptance without depending on Entropy Core at runtime.

Acceptance-Criteria:
  - Receipt examples are YAML/JSON friendly.
  - Each receipt names actor, claim/action, evidence, verifier, status, and
    failure handling.
  - Docs state that Entropy Core may later validate receipts optionally.

Integration-Points:
  - `docs/runtime_verification_protocol.md`
  - `docs/provider_routing_policy.md`
  - `docs/cognition_layer_integrity.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/verify_playbook.py --root .`

### AWP-EL-002: Diverse Review Principle

Owner: codex
Type: docs review
Status: planned

Objective: |
  Add a narrow principle from Gensyn-style diversity research: high-risk work
  benefits from diverse candidate reasoning and independent referee review.

Acceptance-Criteria:
  - Docs explain role/model diversity as a review/evaluation pattern.
  - Swarm behavior, distributed training, token incentives, and autonomous
    self-optimization remain out of scope.
  - The principle maps to existing META/ARCH/CODE/CONSOLIDATED review roles.

Integration-Points:
  - `PLAYBOOK.md`
  - `docs/provider_routing_policy.md`
  - `prompts/`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

## Phase PI-1 - Portfolio Integration

### AWP-PI-001: Portfolio Operating Guide

Owner: codex
Type: docs portfolio
Status: planned

Objective: |
  Document how AI Workflow Playbook, Entropy Core, Workflow-To-Agent Studio,
  Training OS, Radar, Telegram Research Agent, and Telegram Trader Intelligence
  fit together.

Acceptance-Criteria:
  - Guide names the source-of-truth repo for each responsibility.
  - It distinguishes framework, product, utility, paused, and archived projects.
  - It does not make Obsidian, Entropy, or Mythos mandatory dependencies.

Integration-Points:
  - `docs/PROJECT_PLAN.md`
  - `docs/cognition_layer_integrity.md`
  - `engineering-cognition-vault`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-002: Lightweight Adoption Path

Owner: codex
Type: docs migration
Status: done 2026-06-09

Objective: |
  Define a lighter adoption path for projects that only need task state,
  verification records, and review checklists.

Acceptance-Criteria:
  - Migration notes list minimal, standard, and strict adoption sets.
  - Existing paused/reference projects can use minimal mode.
  - Strict mode remains available for high-risk agent/tooling systems.

Integration-Points:
  - `docs/usage_guide.md`
  - `docs/project_fit_guide.md`
  - `templates/`

Implementation-Notes: |
  Added `docs/adoption_modes.md` and updated README, PLAYBOOK, usage guide,
  Orchestrator, and Phase 1 Validator to treat Lean / Standard / Strict as
  real mode-specific paths rather than one full artifact set with softer
  language.

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-003: Solution Reference Catalog And Dynamic Workflow Policy

Owner: codex
Type: docs reference
Status: done 2026-06-09

Objective: |
  Preserve useful external references such as Hermes, Mythos, Entropy, Gensyn,
  Cybos, Claude dynamic workflows, and public workflow examples without making
  them mandatory playbook dependencies.

Acceptance-Criteria:
  - Dynamic workflows are described as optional executable orchestration
    references, not base-path requirements.
  - External references are cataloged by problem solved, useful pattern,
    authority level, and URL.
  - Public workflows require review before adaptation.
  - The playbook keeps generic principles in the base path and points advanced
    runtime/proof/swarm patterns to the reference catalog.

Integration-Points:
  - `docs/dynamic_workflow_reference_policy.md`
  - `reference/solution_references.md`
  - `README.md`
  - `reference/optional_skills.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-004: AI Cost Budget Guardrails

Owner: codex
Type: docs governance
Status: done 2026-06-09

Objective: |
  Make AI/model cost a first-class workflow constraint across bootstrap,
  validation, orchestration, review, and external research references.

Acceptance-Criteria:
  - Cost budget policy defines when inline budget is enough and when
    downstream docs/COST_BUDGET.md is required.
  - Strategist and bootstrap commands collect AI/model budget before generating
    the selected mode's starter package.
  - Phase 1 Validator and Orchestrator flag missing budgets, model escalation,
    retry/fan-out expansion, and dynamic workflow cost drift.
  - Provider-agnostic telemetry has a JSONL entry contract and rollup command
    for CI/review thresholds.
  - Downstream projects have a provider-boundary adapter template and
    `cost:telemetry` task type.
  - External research sources are cited in the cost guardrails research file.

Integration-Points:
  - `docs/cost_budget_guardrails.md`
  - `templates/COST_BUDGET.md`
  - `templates/COST_TELEMETRY_ENTRY.json`
  - `templates/COST_TELEMETRY_ADAPTER.md`
  - `schemas/cost_telemetry_entry.schema.json`
  - `tools/cost_rollup.py`
  - `docs/cost_telemetry_protocol.md`
  - `reference/cost_guardrails_research.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/cost_rollup.py --input /tmp/missing-cost.jsonl --output /tmp/ai_cost_rollup.md`

### AWP-PI-005: AI Cost Architecture And Router Evaluation

Owner: codex
Type: docs governance
Status: done 2026-06-19

Objective: |
  Move cost controls beyond budget policy by adding an enforceable AI cost
  architecture artifact for workload classes, cache layout, batch lanes,
  routing maturity, cascades, and cost-per-successful-task.

Acceptance-Criteria:
  - `docs/ai_cost_architecture.md` defines when cost architecture is required
    and separates architecture boundaries from provider/model routing details.
  - `docs/cache_context_layout.md` defines stable-prefix and volatile-suffix
    prompt caching rules.
  - `templates/COST_ARCHITECTURE.md` and `templates/ROUTER_EVAL.md` provide
    downstream project artifacts.
  - Provider routing policy includes a maturity ladder and gates dynamic
    routing/cascades behind project eval evidence.
  - Strategist, Phase 1 Validator, Orchestrator, strategy review, code review,
    and consolidated review prompts check cost architecture and router eval
    requirements.
  - Usage docs and templates expose the new artifacts during new-project and
    retrofit setup.

Integration-Points:
  - `docs/ai_cost_architecture.md`
  - `docs/cache_context_layout.md`
  - `docs/provider_routing_policy.md`
  - `docs/cost_budget_guardrails.md`
  - `templates/COST_ARCHITECTURE.md`
  - `templates/ROUTER_EVAL.md`
  - `templates/ARCHITECTURE.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `templates/COST_BUDGET.md`
  - `templates/tasks_schema.md`
  - `docs/usage_guide.md`
  - `reference/cost_guardrails_research.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/PROMPT_S_STRATEGY.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/integrity_check.py --root .`

### AWP-PI-006: External Skill Security Gate

Owner: codex
Type: docs governance
Status: done 2026-06-19

Objective: |
  Add a bounded security gate for third-party and cross-project agent skills so
  skills cannot enter project or global agent context without source,
  capability, scan, signature/hash, install-scope, and risk-triage evidence.

Acceptance-Criteria:
  - `docs/external_skill_security_policy.md` defines the external skill trust
    gate and maps SkillSpector/NVIDIA trust-pipeline patterns into playbook
    artifacts.
  - `templates/EXTERNAL_SKILL_TRUST_RECORD.md` provides a downstream evidence
    artifact for source pin/signature/hash, capabilities, scan evidence,
    findings triage, install scope, architecture impact, and approval.
  - Optional skill registry includes an External Skill Security Gate descriptor.
  - Task schema includes `Type: skill:security`.
  - Orchestrator, Phase 1 Validator, CODE review, consolidated review,
    Strategist, adoption docs, and templates check external skill trust records
    before install/update/enablement.
  - External references cite SkillSpector, NVIDIA skill trust docs, and the
    Agent Skills in the Wild paper as evidence for mandatory vetting.

Integration-Points:
  - `docs/external_skill_security_policy.md`
  - `templates/EXTERNAL_SKILL_TRUST_RECORD.md`
  - `templates/skills/external_skill_security_skill.md`
  - `reference/optional_skills.md`
  - `reference/solution_references.md`
  - `templates/IMPLEMENTATION_CONTRACT.md`
  - `templates/tasks_schema.md`
  - `templates/PROJECT_BRIEF.md`
  - `docs/adoption_modes.md`
  - `docs/usage_guide.md`
  - `README.md`
  - `prompts/STRATEGIST.md`
  - `prompts/PHASE1_VALIDATOR.md`
  - `prompts/ORCHESTRATOR.md`
  - `prompts/audit/PROMPT_2_CODE.md`
  - `prompts/audit/PROMPT_3_CONSOLIDATED.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 tools/skill_security_gate.py --root . --discover-agent-skills`

### AWP-PI-007: Bootstrap And Guardrail Automation

Owner: codex
Type: tools automation
Status: done 2026-06-19

Objective: |
  Close the remaining procedural gaps by adding deterministic helpers for
  project bootstrap, external skill security CI enforcement, and provider-
  neutral AI cost telemetry adapter scaffolding.

Acceptance-Criteria:
  - `tools/init_playbook_project.py` initializes Lean / Standard / Strict
    downstream projects without overwriting existing files by default.
  - `tools/skill_security_gate.py` discovers agent skill directories, requires
    trust records, invokes SkillSpector when skills are present, parses JSON
    scan output, writes optional SARIF, and blocks unresolved high-risk findings.
  - `templates/cost_adapters/python/telemetry_adapter.py` provides a concrete
    provider-neutral adapter for writing cost telemetry JSONL entries from
    common provider/gateway usage objects.
  - CI template and playbook repo workflow run the new deterministic checks.
  - Usage docs, tools docs, roadmap, and known-gaps sections describe the new
    practical path and remaining optional provider-specific work.

Integration-Points:
  - `tools/init_playbook_project.py`
  - `tools/skill_security_gate.py`
  - `templates/TASKS.md`
  - `templates/cost_adapters/`
  - `.github/workflows/playbook-checks.yml`
  - `ci/ci.yml`
  - `docs/usage_guide.md`
  - `docs/external_skill_security_policy.md`
  - `docs/cost_telemetry_protocol.md`
  - `tools/README.md`
  - `PLAYBOOK.md`

Verification:
  - `python3 tools/playbook_validate.py --root . --check tasks`
  - `python3 -m py_compile tools/*.py`
