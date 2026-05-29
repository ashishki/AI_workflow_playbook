# AI Workflow Playbook Tasks

Status: active core framework task graph
Last updated: 2026-05-29

This file tracks framework work for the playbook itself. It is separate from
project adoption tasks in downstream repositories.

## Active Direction

Preserve the playbook as a governance-first, deterministic-first, artifact-first
engineering workflow. Do not turn it into a required runtime, orchestration
server, or Mythos/Entropy clone.

## Phase ZT-1 - Zero-Trust Execution Consolidation

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
  - `prompts/PROMPT_2_CODE.md`
  - `prompts/PROMPT_3_CONSOLIDATED.md`
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

### AWP-PI-002: Lightweight Adoption Path

Owner: codex
Type: docs migration
Status: planned

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
