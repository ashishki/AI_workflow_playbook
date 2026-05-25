# Cognition Manifest - AI Workflow Playbook

---
artifact_kind: retrieval_manifest
project: ai-workflow-playbook
source_repo: AI_workflow_playbook
status: active
canonical: false
generated: false
tags: [playbook, cognition, governance]
---

Version: 1.0
Last updated: 2026-05-25

## Purpose

Repo-local map for the playbook's cognition and operational memory extension. This file helps agents find the architecture, retrieval, Obsidian, schema, template, and migration surfaces without treating generated artifacts as authority.

## Authority Rules

- `PLAYBOOK.md`, templates, prompts, schemas, tools, and cognition docs are authoritative for this repository.
- Generated manifests and context packets are convenience artifacts only.
- Obsidian is an optional markdown UI and graph browser, not a backend.

## Project Identity

| Field | Value |
|-------|-------|
| Primary shape | Governance-first playbook and markdown cognition toolkit |
| Governance level | Standard |
| Runtime tier | T0 tooling |
| Active profiles | Documentation, retrieval manifests, context packet generation |

## Canonical Truth

| Surface | Path | Notes |
|---------|------|-------|
| Master workflow | `PLAYBOOK.md` | Workflow rules and layer model |
| Readme | `README.md` | User-facing overview |
| Cognition architecture | `docs/cognition/architecture.md` | Operating model |
| Retrieval packets | `docs/cognition/retrieval_context_packets.md` | Retrieval and packet contract |
| Obsidian vault | `docs/cognition/obsidian_vault_architecture.md` | Optional vault structure |
| Git integration | `docs/cognition/git_integration.md` | Sync and generated artifact policy |
| Migration plan | `docs/cognition/migration_plan.md` | Staged rollout |
| Safeguards | `docs/cognition/anti_complexity_safeguards.md` | Complexity ceilings |
| Templates | `templates/`, `templates/cognition/` | Project scaffolding |
| Schemas | `schemas/` | Metadata validation |
| Tools | `tools/` | Deterministic manifest and packet builders |

## Retrieval Scopes

| Scope | Start here | Include next |
|-------|------------|--------------|
| Cognition architecture | `docs/cognition/architecture.md` | safeguards, git integration |
| Obsidian design | `docs/cognition/obsidian_vault_architecture.md` | vault template |
| Context packet tooling | `docs/cognition/retrieval_context_packets.md` | tools and schemas |
| Project migration | `docs/cognition/migration_plan.md` | current project assessment, manifest template |
| Playbook prompt update | `prompts/`, `templates/` | architecture and contract docs |

## Known Gaps

| Gap | Impact | Migration step |
|-----|--------|----------------|
| No committed generated index yet | Tool output not visible until generated | Generate locally or in CI when adoption begins |
| No Obsidian vault repo yet | Graph browsing remains documented only | Create external vault after repo-local manifests stabilize |

## Generated Artifacts

| Artifact | Path | Policy |
|----------|------|--------|
| Cognition index | `generated/cognition/index.json` | Optional generated artifact |
| Context packets | `docs/context-packets/` | Commit only major design/review packets |

