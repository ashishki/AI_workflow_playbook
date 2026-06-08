# Cognition Manifest - {{PROJECT_NAME}}

Version: 1.0
Last updated: {{DATE}}

---

## Purpose

This file is the repo-local map for operational engineering memory. It helps humans and agents find canonical architecture, decisions, evals, findings, evidence, and context-packet entry points without relying on chat memory or Obsidian.

This file is a retrieval surface. It is not a replacement for canonical artifacts.

---

## Authority Rules

- Repo artifacts are authoritative.
- README files are local navigation indexes, not authority over canonical
  architecture, contract, tasks, ADRs, evals, proof, or reviews.
- Obsidian and generated indexes are navigation layers only.
- If this manifest conflicts with architecture, contract, ADRs, evals, tests, or audit reports, the canonical artifact wins.
- Generated context packets must cite canonical paths.
- The cognition vault is used for navigation, context packets, and cross-project recall only. Project files remain authoritative.

---

## Project Identity

| Field | Value |
|-------|-------|
| Project | {{PROJECT_NAME}} |
| Repository | {{REPO_NAME}} |
| Governance level | {{Lean \| Standard \| Strict}} |
| Runtime tier | {{T0 \| T1 \| T2 \| T3}} |
| Primary shape | {{deterministic \| workflow \| bounded tool-use \| agentic \| hybrid}} |
| Active profiles | {{RAG, Tool-Use, Agentic, Planning, Compliance, or none}} |

---

## Canonical Truth

| Surface | Path | Notes |
|---------|------|-------|
| README indexes | `README.md`, `docs/README.md`, folder READMEs | {{navigation only}} |
| Architecture | `docs/ARCHITECTURE.md` | {{notes}} |
| Contract | `docs/IMPLEMENTATION_CONTRACT.md` | {{notes}} |
| Task graph | `docs/tasks.md` | {{notes}} |
| Session state | `docs/CODEX_PROMPT.md` | {{notes}} |
| Decisions | `docs/DECISION_LOG.md`, `docs/adr/` | {{notes}} |
| Eval artifacts | `docs/*_eval.md` | {{notes}} |
| Evidence index | `docs/EVIDENCE_INDEX.md` | {{notes}} |
| Reviews | `docs/audit/`, `docs/archive/` | {{notes}} |

---

## Retrieval Scopes

| Scope | Start here | Include next |
|-------|------------|--------------|
| Architecture change | `docs/ARCHITECTURE.md`, `docs/DECISION_LOG.md` | relevant ADRs, evals, open findings |
| Eval regression | affected `docs/*_eval.md` | evidence rows, prior review, task that changed boundary |
| Reviewer packet | current task + contract | evidence, evals, ADR lineage, prior findings |
| Orchestrator packet | `docs/CODEX_PROMPT.md`, `docs/tasks.md` | Context-Refs, journal, evidence index |
| Postmortem | failing eval/test/review | timeline, ADRs, prior findings, corrective tasks |

---

## Local/VPS Agent Context Workflow

Agents do not automatically discover the cognition vault. The operator or
orchestrator must pass a repo-local manifest, project map, or generated context
packet path into the agent task.

Expected sibling layout:

```text
ai-stack/
|-- projects/{{REPO_NAME}}/
`-- engineering-cognition-vault/
```

Local project work:

```bash
cd ai-stack/engineering-cognition-vault
./scripts/sync_from_projects.sh --no-pull --commit --push
```

Before review, ensure this project has a fresh vault index:

```bash
cd ai-stack/engineering-cognition-vault
./scripts/ensure_fresh_for_project.sh {{PROJECT_SLUG}} --no-pull --commit --push
```

VPS project work:

1. Commit and push code, docs, evals, ADRs, findings, or postmortems in this repo.
2. Refresh the vault on the machine that owns vault sync:

```bash
cd ai-stack/engineering-cognition-vault
git pull --ff-only
./scripts/sync_from_projects.sh --commit --push
```

If an agent runs on the VPS, clone the vault next to `projects/` and pass packet
paths explicitly:

```text
../engineering-cognition-vault/10-projects/{{PROJECT_SLUG}}.md
../engineering-cognition-vault/90-context-packets/<role>-{{PROJECT_SLUG}}-<scope>.md
```

Do not write canonical decisions, eval results, or findings directly into the
vault. Write them into this repo first, then regenerate the vault.

Use the vault when starting an agent cold, preparing a review packet, comparing
projects, or checking cross-project dependencies. Do not use it to close tasks,
change project status, replace ADRs/evals/findings, or drive runtime behavior.

---

## Known Gaps

| Gap | Impact | Migration step |
|-----|--------|----------------|
| {{gap}} | {{impact}} | {{step}} |

---

## Generated Artifacts

| Artifact | Path | Policy |
|----------|------|--------|
| Cognition index | `generated/cognition/index.json` | generated, optional to commit |
| Context packets | `docs/context-packets/` | commit only major review/incident packets |
| Obsidian notes | external vault or `_generated/` | never authoritative |

---

## Commands

Generate deterministic index:

```bash
python3 tools/cognition_index.py --root . --output generated/cognition/index.json
```

Build reviewer packet:

```bash
python3 tools/context_packet_builder.py \
  --manifest generated/cognition/index.json \
  --role reviewer \
  --scope "{{scope}}" \
  --output docs/context-packets/reviewer-{{scope_slug}}.md
```
