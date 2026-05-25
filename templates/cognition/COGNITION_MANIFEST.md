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
- Obsidian and generated indexes are navigation layers only.
- If this manifest conflicts with architecture, contract, ADRs, evals, tests, or audit reports, the canonical artifact wins.
- Generated context packets must cite canonical paths.

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

