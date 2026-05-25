# Current Project Cognition Assessment

Date: 2026-05-25
Scope: repositories under `~/Documents/dev/ai-stack/projects/` named in the cognition-layer request.

---

## Summary

The portfolio already has strong playbook adoption in most active repos: architecture docs, contracts, task graphs, eval artifacts, audit archives, ADRs, and implementation journals are common. The main missing layer is a consistent repo-local cognition manifest and a standard context-packet contract.

The migration should therefore be additive. Do not refactor runtime code or rewrite existing governance docs just to fit a new taxonomy.

---

## Project-by-Project Findings

| Project | Current architecture | Existing memory/eval surfaces | Main gaps | Implemented migration |
|---------|----------------------|-------------------------------|-----------|----------------------|
| `Entropy_Protocol` | Portfolio repo with product workspaces: entropy core, trader risk audit, signal analytics sandbox | Product-level playbooks, ADRs, evals, audits, evidence-heavy demos | Root-level cross-product cognition map missing; product boundaries need explicit retrieval scopes | Add root `docs/COGNITION_MANIFEST.md` mapping product workspaces and cross-product retrieval |
| `AI-Rollout-Training-OS` | FastAPI/Postgres training adoption OS with text-only RAG and deterministic workflow states | Full playbook docs, retrieval eval, evidence index, audit phases, CI | Needs manifest tying adoption hypothesis, RAG eval, manager approval evidence, and review packets | Add `docs/COGNITION_MANIFEST.md` |
| `Demand-to-MVP-Radar` | Local CLI/batch workflow for source-grounded MVP opportunity ranking | Strong decision memory, retrieval/tool evals, evidence ledger, audit archive, source catalog | Dirty active work; needs non-invasive manifest and future packet scopes for source trust/retrieval regressions | Add `docs/COGNITION_MANIFEST.md` only |
| `Lead-Response-SLA-Agent` | Multi-tenant FastAPI service with RAG, tool-use, bounded agent loop, CRM/calendar/messaging side effects | Active eval artifacts, evidence index, ADRs, audit archive, runbooks, market proof docs | Needs high-risk packet scopes for tenant isolation, unsafe tools, retrieval no-answer behavior, and pilot evidence | Add `docs/COGNITION_MANIFEST.md` |
| `-Workflow-to-Agent-Studio` | Local-first workflow-to-agent blueprint generator with ingestion, retrieval, plan eval, markdown export | Playbook docs, retrieval/plan evals, evidence packs, audit archive, product strategy | Needs graph links from public-source experiments to decisions/evals; context packet scopes for blueprint quality reviews | Add `docs/COGNITION_MANIFEST.md` |
| `Dream_Motif_Interpreter` | Private single-user FastAPI/Telegram/RAG system with Google Docs, pgvector, voice, motif research | Extensive ADR lineage, retrieval eval, evidence index, phased tasks, runbooks, audit archives | Mature project but needs manifest to separate personal domain memory from engineering cognition | Add `docs/COGNITION_MANIFEST.md` |
| `telegram-research-agent` | Private single-user Telegram research intelligence pipeline with deterministic scoring and scoped evidence memory | Strong runtime memory architecture docs, decision journal, evidence DB, operator workflow, archive | Missing playbook-style decision/evidence indexes and ADR lineage; manifest should map existing memory to playbook concepts | Add `docs/COGNITION_MANIFEST.md` |
| `gdev-agent` | Multi-tenant support triage service with tool loop, approvals, RLS, eval API, observability stack | Architecture, contract, eval docs, audit reports, dev logs | Missing decision log, implementation journal, evidence index, ADR directory, and cognition manifest | Add `docs/COGNITION_MANIFEST.md`; future migration should add decision/evidence/journal surfaces |
| `film-school-assistant` | Private single-user Telegram assistant with SQLite memory, confirmations, voice, reminders | Architecture, memory architecture, decisions doc, workflow boundaries, archived evals/reviews | Needs playbook-native evidence index and ADR lineage; manifest should keep creative memory separate from engineering memory | Add `docs/COGNITION_MANIFEST.md` |
| `AI_Adoption_Diff_Tool` | Draft deterministic CLI analytics tool for before/after AI adoption analysis | Phase 1 architecture, contract, tasks, prompt, project brief | No runtime code yet; missing decision log, journal, evidence index, manifest, README | Add `docs/COGNITION_MANIFEST.md`; future bootstrap should add decision/journal/evidence templates before implementation |

---

## Cross-Project Pattern Candidates

Create cross-project pattern notes only after at least two project artifacts are linked as evidence.

| Pattern | Candidate projects | Why useful |
|---------|-------------------|------------|
| Text-only RAG with `insufficient_evidence` | Dream Motif, AI Rollout OS, Demand Radar, Lead SLA, Workflow Studio | Common eval and safety pattern |
| Deterministic scoring before LLM synthesis | Demand Radar, Telegram Research Agent, AI Adoption Diff Tool | Preserves auditability and avoids vague ranking |
| Bounded side-effecting tool-use | Lead SLA, gdev-agent, Demand Radar | Unsafe action gates and audit trails recur |
| Private single-user assistant memory | Dream Motif, Film School Assistant, Telegram Research Agent | Separates personal domain memory from engineering governance memory |
| Evidence-first market validation | Demand Radar, Lead SLA, AI Rollout OS, Workflow Studio | Links product hypotheses to proof artifacts |

---

## Migration Priorities

1. Add repo-local cognition manifests everywhere.
2. Generate deterministic indexes only for repos with enough docs volume to justify it.
3. Add context packets for new phase reviews, eval regressions, and architecture changes.
4. Backfill ADR/evidence indexes only where missing and currently active. Do not reconstruct all old history.
5. Build optional Obsidian project maps from manifests after repo-local surfaces exist.

---

## Risks

- Dirty active repos should not have existing modified files touched by the cognition migration.
- Mature repos should not be forced into a new directory taxonomy.
- Private personal-assistant projects must not leak domain/user memory into cross-project engineering graph notes.
- Cross-project notes must cite canonical artifacts and remain patterns, not authority.

