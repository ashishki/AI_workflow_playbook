# Obsidian Vault Architecture

Version: 1.0
Last updated: 2026-05-25

---

## Role of Obsidian

Obsidian is a markdown UI and graph browser for cognition artifacts. It is not the backend, not runtime infrastructure, and not authoritative memory.

The vault must remain portable:

- files are plain markdown
- links are relative markdown links where practical
- generated notes identify their source path
- retrieval scripts work without Obsidian running
- cloud sync is optional and non-authoritative

---

## Recommended Vault Root

Use a separate Git repository or a top-level sibling directory:

```text
engineering-cognition-vault/
|-- 00-operating-model/
|-- 10-projects/
|-- 20-decisions/
|-- 30-evals/
|-- 40-findings/
|-- 50-patterns/
|-- 60-research/
|-- 70-postmortems/
|-- 80-agent-profiles/
|-- 90-context-packets/
|-- _generated/
`-- _templates/
```

The vault can also live inside a mono-repo, but it should not replace project-local canonical docs. Project repos remain authoritative.

---

## Directory Contract

| Directory | Manual or generated | Purpose |
|-----------|---------------------|---------|
| `00-operating-model/` | Manual | Vault rules, sync policy, graph conventions |
| `10-projects/` | Mixed | One project map per repo, with links to canonical artifacts |
| `20-decisions/` | Mixed | Cross-project decision browser and ADR indexes |
| `30-evals/` | Mixed | Eval baselines, regressions, and comparison maps |
| `40-findings/` | Mixed | Persistent finding indexes and recurring issue maps |
| `50-patterns/` | Manual | Reusable engineering patterns and anti-patterns |
| `60-research/` | Manual | Source-grounded research notes linked to decisions |
| `70-postmortems/` | Manual | Incident and regression postmortems |
| `80-agent-profiles/` | Manual | Role-specific context and authority boundaries |
| `90-context-packets/` | Generated | Bounded packets for strategists, reviewers, implementers |
| `_generated/` | Generated | Machine indexes and mirror notes |
| `_templates/` | Manual | Note templates copied from the playbook |

---

## Naming Conventions

Use stable, path-friendly names:

```text
10-projects/lead-response-sla-agent.md
20-decisions/ADR-004-deployment-target.md
30-evals/lead-response-sla-agent-retrieval-eval.md
40-findings/lead-response-sla-agent-open-findings.md
50-patterns/text-only-rag-with-insufficient-evidence.md
50-patterns/anti-pattern-vector-memory-as-authority.md
70-postmortems/2026-05-25-retrieval-regression.md
90-context-packets/reviewer-lead-response-sla-agent-T21.md
```

Do not use date-heavy names except for postmortems and generated context packets where freshness matters.

---

## Project Map Template

Every project note in `10-projects/` should be short and linked:

```yaml
---
artifact_kind: project_map
project: lead-response-sla-agent
source_repo: Lead-Response-SLA-Agent
canonical: false
generated: false
status: active
tags: [project, ai-workflow-playbook]
---
```

Required sections:

- `Canonical Truth`
- `Active Capability Profiles`
- `Decision Lineage`
- `Eval Memory`
- `Open Findings`
- `Context Packet Scopes`
- `Migration Notes`

The project map should not duplicate full architecture. It links to `docs/ARCHITECTURE.md` and summarizes only retrieval-critical facts.

---

## Link Strategy

Use three link classes:

| Link class | Format | Use |
|------------|--------|-----|
| Canonical file link | `repo://Lead-Response-SLA-Agent/docs/ARCHITECTURE.md` in generated notes, or relative markdown links inside the repo | Points to authoritative source |
| Vault note link | `[[text-only-rag-with-insufficient-evidence]]` | Cross-project navigation |
| Evidence citation | `docs/retrieval_eval.md#Evaluation-History` | Eval and review evidence |

`repo://` is a convention for generated notes, not a runtime dependency. Tools may render it as text, a local absolute path, or a GitHub URL.

---

## Generated vs Manual Rules

Generated notes:

- live under `_generated/` or `90-context-packets/`
- include `generated: true`
- include `source_repo` and `source_path` or `source_manifest`
- may be deleted and rebuilt
- must not contain unreviewed decisions

Manual notes:

- capture reusable patterns, postmortems, research synthesis, and explicit cross-project decisions
- must link to canonical project artifacts
- should be reviewed like docs when they change behavior

Do not manually edit generated notes. Fix the canonical artifact or generation rule, then regenerate.

---

## Graph Boundaries

Use graph boundaries to prevent the vault from becoming a personal second brain:

- include only operational engineering cognition
- exclude daily notes, general journaling, personal productivity logs, and unbounded chat history
- exclude raw secrets, credentials, private tokens, and unredacted customer data
- exclude generated dependency trees and build outputs
- include only cross-project notes that have clear reuse value

Graph growth ceiling:

- one project map per repo
- one pattern note per reusable pattern
- one anti-pattern note per recurring failure mode
- one generated context packet per meaningful task/review, not every conversation
- no semantic-only edges in the committed graph

---

## Optional Sync

Allowed sync mechanisms:

- Git remote
- Obsidian Sync
- Syncthing
- encrypted cloud backup

Rules:

- sync failure must not block development
- no CI or retrieval script depends on Obsidian Sync
- generated indexes can be rebuilt from repositories
- private vault data must follow the strictest source repo privacy policy represented in the vault
