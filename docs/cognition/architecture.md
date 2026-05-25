# Cognition Layer Architecture

Version: 1.0
Last updated: 2026-05-25

---

## Purpose

The cognition layer is a portable markdown operating layer for long-lived engineering context. It helps humans and agents recover architectural intent, decision lineage, evidence, findings, eval history, hypotheses, and project continuity without treating chat memory or a note-taking app as authority.

This is not a generic PKM system. It is operational engineering memory for repositories that already follow the AI Workflow Playbook.

---

## Core Invariant

The repository remains the source of truth.

Obsidian, vector stores, dashboards, and generated indexes are navigation surfaces only. If they disagree with canonical repo artifacts, the repo artifact wins and the generated surface must be corrected or regenerated.

Canonical artifacts include:

- code, tests, migrations, fixtures, and CI
- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/tasks.md`
- `docs/CODEX_PROMPT.md`
- `docs/adr/*.md`
- `docs/*_eval.md`
- `docs/audit/*` and archived review reports
- `docs/DECISION_LOG.md`
- `docs/IMPLEMENTATION_JOURNAL.md`
- `docs/EVIDENCE_INDEX.md`
- project-local runbooks, incident reports, and postmortems

Convenience artifacts include:

- `docs/COGNITION_MANIFEST.md`
- generated cognition indexes
- generated context packets
- Obsidian graph notes
- semantic search indexes
- cross-project pattern notes

Convenience artifacts must never override canonical artifacts.

---

## Layer Model

| Layer | Responsibility | Authority |
|-------|----------------|-----------|
| Repo truth | Code, docs, tests, ADRs, evals, reviews | Authoritative |
| Operational memory | Decision, evidence, journal, finding, hypothesis, postmortem surfaces | Authoritative only when they are the canonical artifact for that record |
| Retrieval manifest | Deterministic map of important files, sections, tags, and graph edges | Generated or curated convenience |
| Context packets | Bounded role-specific bundles for agents and reviewers | Convenience; cites canonical paths |
| Obsidian vault | Human graph browser and markdown UI | Convenience |
| Semantic index | Optional recall over selected markdown/code artifacts | Supplemental only |

The system must work if Obsidian is closed, unavailable, or never installed.

---

## Memory Types

| Type | Stored as | Purpose | Required fields |
|------|-----------|---------|-----------------|
| Decision | ADR + `DECISION_LOG.md` row | Preserve architectural tradeoffs and supersession | ID, status, date, decision, canonical source, supersedes |
| Finding | Review report + `CODEX_PROMPT.md` open finding | Preserve defects, severity, lifecycle, and evidence | ID, severity, source review, status, owner, evidence |
| Eval memory | `*_eval.md` and evidence index row | Track baselines, regressions, and experiment changes | profile, metric, baseline, current, source, date |
| Hypothesis | hypothesis note or eval section | Track product/architecture assumptions and outcome | statement, evidence needed, state, decision link |
| Postmortem | `docs/postmortems/*.md` | Preserve incidents and recurrence prevention | impact, cause, detection, actions, evidence |
| Research | `docs/research/*.md` | Ground non-trivial external choices | source list, findings, caveats, consuming decision |
| Pattern | cross-project note | Reuse engineering patterns with constraints | problem, context, solution, projects, counterexamples |
| Anti-pattern | cross-project note | Prevent repeated mistakes | failure mode, trigger, detection, safer replacement |
| Agent profile | markdown note | Define role-scoped context expectations | role, reads, writes, forbidden actions, packet scope |

---

## Artifact Taxonomy

Use these `artifact_kind` values in frontmatter and generated indexes:

| `artifact_kind` | Examples |
|-----------------|----------|
| `architecture` | `docs/ARCHITECTURE.md`, architecture maps |
| `contract` | `docs/IMPLEMENTATION_CONTRACT.md` |
| `task_graph` | `docs/tasks.md`, archived task graphs |
| `session_state` | `docs/CODEX_PROMPT.md` |
| `decision_log` | `docs/DECISION_LOG.md` |
| `adr` | `docs/adr/ADR-*.md` |
| `journal` | `docs/IMPLEMENTATION_JOURNAL.md` |
| `evidence_index` | `docs/EVIDENCE_INDEX.md` |
| `eval` | `docs/retrieval_eval.md`, `docs/tool_eval.md`, `docs/agent_eval.md` |
| `review` | `docs/audit/*REVIEW*.md` |
| `finding` | standalone finding notes when used |
| `postmortem` | `docs/postmortems/*.md` |
| `hypothesis` | `docs/hypotheses/*.md` |
| `research` | `docs/research/*.md` |
| `runbook` | `docs/runbook.md`, `docs/*RUNBOOK*.md` |
| `context_packet` | generated agent packets |
| `retrieval_manifest` | generated or curated manifest |

Keep the taxonomy small. Add a new kind only when retrieval behavior changes.

---

## Metadata Contract

Markdown notes may include frontmatter, but frontmatter is not required for canonical playbook artifacts. Generated indexes infer basic metadata from file path and headings when frontmatter is absent.

Recommended frontmatter:

```yaml
---
artifact_kind: adr
project: lead-response-sla-agent
status: active
canonical: true
generated: false
source_repo: Lead-Response-SLA-Agent
source_path: docs/adr/ADR-004-deployment-target.md
tags:
  - runtime
  - deployment
related_decisions:
  - D-004
related_evals:
  - docs/agent_eval.md
---
```

Metadata should answer retrieval questions, not become a shadow database. Prefer 5 to 10 fields over large schemas.

---

## Knowledge Graph Strategy

The graph is file-backed and edge-explicit.

Allowed edge sources:

- markdown links
- ADR `Supersedes` / `Superseded by` fields
- `DECISION_LOG.md` canonical source and supersession columns
- `EVIDENCE_INDEX.md` artifact rows
- task `Context-Refs`
- eval `Changed by`, `Eval Source`, and regression notes
- generated manifest links derived from the above

Avoid inferred edges from semantic similarity as authority. Semantic similarity may suggest links, but a human or deterministic script must write a concrete markdown link before agents rely on it.

---

## Retrieval Strategy

Retrieval order is deterministic-first:

1. Current task `Context-Refs`
2. Active state in `docs/CODEX_PROMPT.md`
3. Decision log rows and ADRs
4. Evidence index rows and eval artifacts
5. Recent implementation journal entries
6. Audit/review archives for the same boundary
7. Cross-project pattern notes
8. Optional semantic search over selected markdown

Semantic/vector retrieval is allowed only as supplemental discovery. It must return citations to repo paths and must not inject uncited memory into a context packet.

---

## Context Packet Principle

Agents consume bounded role-specific context packets, not vault dumps.

Each packet must declare:

- role
- task or investigation scope
- source repository
- included artifacts
- excluded surfaces
- canonical evidence paths
- open risks or findings
- freshness note

Packets should cite paths and include short excerpts only when the excerpt changes behavior. Large canonical docs stay linked unless the task is high-risk and compression would hide a critical rule.

---

## Ingestion Pipeline

Minimum viable ingestion:

1. scan repo files with deterministic path rules
2. classify artifact kind by path and filename
3. parse frontmatter if present
4. parse headings and markdown links
5. calculate stable content hash
6. emit `generated/cognition/index.json`
7. optionally sync selected markdown files into an Obsidian vault as links or generated notes

Do not ingest private secrets, `.env`, raw chat logs, build artifacts, dependency caches, database dumps, or large media unless an explicit evidence policy requires it.

---

## Governance Rules

- A cognition artifact that changes implementation behavior must be committed with the code or docs it supports.
- ADR lineage is append-only. Supersede instead of deleting.
- Eval memory must record the exact eval source and date. Missing source means invalid eval memory.
- Findings remain lifecycle-managed by severity and age cap. Do not bury findings in graph notes.
- Generated files must be clearly marked `generated: true` or stored under `generated/`.
- Obsidian-specific configuration is optional and must not be required for CI, tests, or retrieval scripts.

