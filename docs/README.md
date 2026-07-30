# Documentation Index

Status: navigation index, not authority
Last updated: 2026-07-30

Canonical authority remains in the named documents, schemas, tools, prompts,
and evidence artifacts. This index is only a routing surface so humans and
agents do not load every Markdown file by default.

## Core Workflow

- `../README.md` - user-facing overview and quick-start map.
- `../PLAYBOOK.md` - master workflow contract and authority model.
- `usage_guide.md` - end-to-end operating guide for new and retrofit projects.
- `adoption_modes.md` - Lean-Core / Standard / Strict proportionality matrix.
- `project_fit_guide.md` - problem-first adoption gate and anti-patterns.
- `tasks.md` - active framework task graph for this repository.
- `PROJECT_PLAN.md` - current maintainer roadmap.
- `codex_exec_subagent_protocol.md` - optional isolated `codex exec` reviewer
  and fix-agent protocol.
- `LEGAL_STATUS.md` - repository license and legal status.

## Planning And Feature Workflow

- `adr/ADR-002-feature-design-companion-json.md` - decision for paired Feature
  Design Markdown plus companion JSON registry.
- `../templates/PROJECT_BRIEF.md` - source template copied into generated
  projects as `docs/PROJECT_BRIEF.md`.
- `../templates/FEATURE_DESIGN.md` - source template for
  `docs/design/<feature-id>.md`.
- `../schemas/feature_design.schema.json` - deterministic design registry and
  slice contract.
- `../schemas/task.schema.json` - task metadata contract, including Planning
  Depth and slice fields.
- `../schemas/instruction_manifest.schema.json` - context-loading manifest
  contract.
- `../tools/feature_workflow.py` - thin workflow entrypoint for
  `plan -> draft -> review -> approve -> next -> start -> context -> check`.

## State And Evidence

- `CODEX_PROMPT.md` - compact session state for this repository.
- `DECISION_LOG.md` - append-only decision index; ADRs remain the detailed
  authority.
- `IMPLEMENTATION_JOURNAL.md` - durable implementation notes.
- `EVIDENCE_INDEX.md` - committed evidence index.
- `../reports/README.md` - evidence archive index. Do not load trial-level
  `reports/**` by default.

## Testing And Evaluation

- `testing/test_first_protocol.md` - risk-tiered test-first implementation
  protocol.
- `testing/holdout_acceptance.md` - holdout gate policy.
- `testing/property_and_mutation_oracles.md` - stronger test-oracle guidance.
- `testing/ui_verification.md` - UI and visual verification protocol.
- `evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md` - empirical claim boundaries.
- `evaluation/CI_EVAL_GATE.md` - CI/eval gate policy.
- `evaluation/CRITIC_CALIBRATION.md` - critic calibration policy.
- `evaluation/TEST_FIRST_PILOT_PLAN.md` and
  `evaluation/TEST_FIRST_PILOT_RESULTS.md` - historical first pilot plan and
  result.

## RAG Evaluation v2

- `research/rag-eval-2026.md` - source-grounded RAG research note.
- `adr/ADR-001-rag-evaluation-v2.md` - architecture decision.
- `rag/RAG_DATA_READINESS.md` - Stage 0 corpus and ingestion readiness.
- `rag/RETRIEVAL_EVAL_PLAN.md` - retrieval stage model and baseline matrix.
- `rag/GENERATION_EVAL_PLAN.md` - generation, citations, abstention, and judge
  policy.
- `rag/RAG_ACCEPTANCE_CRITERIA.md` - stop-ship rules and maturity language.
- `rag/RAG_EVAL_TOOL_ADAPTERS.md` - external scorer adapter guidance.
- `../schemas/rag_eval_manifest.schema.json`,
  `../schemas/rag_eval_case.schema.json`,
  `../schemas/rag_eval_observation.schema.json`,
  `../schemas/rag_eval_result.schema.json`, and
  `../schemas/rag_eval_comparison.schema.json` - machine-readable contracts.
- `../tools/rag_eval_validate.py`, `../tools/rag_eval_score.py`, and
  `../tools/rag_eval_compare.py` - offline deterministic tools.

Mechanism fixtures and examples are not empirical product evidence.

## Harness And Agentic Systems

- `agent_harness/HARNESS_EVALUATION_PROTOCOL.md` - authoritative harness
  evaluation boundary.
- `agent_harness/AGENT_TRACE_SCHEMA.md`,
  `agent_harness/ERROR_RECOVERY_PLAYBOOK.md`,
  `agent_harness/HUMAN_IN_THE_LOOP_POLICY.md`, and
  `agent_harness/TOOL_PERMISSION_POLICY.md` - optional reference surfaces for
  agentic/tool-use projects.
- `../companion/ai_workflow_harness_lab/README.md` - runnable companion harness
  package.

## Cost, Runtime, And Security

- `cost_budget_guardrails.md` - budget boundary policy.
- `ai_cost_architecture.md` - AI cost architecture for recurring/material AI
  work.
- `cost_telemetry_protocol.md` - provider-neutral cost telemetry contract.
- `cache_context_layout.md` - prompt cache stable-prefix / volatile-suffix
  rules.
- `external_skill_security_policy.md` - external skill trust gate.
- `runtime_verification_protocol.md`,
  `filesystem_reality_principle.md`, and `bounded_correction_turns.md` -
  zero-trust execution references.
- `autonomous_workflows/` - optional routine/cron/webhook workflow pack, not
  default Playbook runtime.

## Cognition Layer

- `COGNITION_MANIFEST.md` - repo-local map for cognition and context packet
  surfaces; not an authority layer.
- `cognition/architecture.md` - cognition layer architecture.
- `cognition/retrieval_context_packets.md` - generated context packet model.
- `cognition/vault_usage_protocol.md` and
  `cognition/obsidian_vault_architecture.md` - optional vault guidance.
- `cognition/git_integration.md`, `cognition/migration_plan.md`, and
  `cognition/anti_complexity_safeguards.md` - optional rollout and safety
  guidance.

## Reference And Archive

- `../reference/` - optional external research, Codex CLI notes, solution
  references, and skill companion docs. These never override core contracts.
- `../domain_packs/` - optional domain packs; not core Playbook policy.
- `../examples/` - examples and fixtures; not proof of production outcomes.
- `../reports/` - committed evidence archive. Start with
  `../reports/README.md` or `EVIDENCE_INDEX.md`, not trial-level files.

## Known Cleanup Rules

- Keep active authority in `README.md`, `PLAYBOOK.md`, `docs/usage_guide.md`,
  `docs/adoption_modes.md`, schemas, tools, ADRs, and current templates.
- Keep compatibility redirects only when they preserve active migration paths.
- Keep historical evidence under `reports/`; do not reference it from hot-path
  docs unless the specific evidence still supports a current claim.
- Do not create placeholder docs only to satisfy a checklist.
