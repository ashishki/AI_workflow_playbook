# Anti-Complexity Safeguards

Version: 1.0
Last updated: 2026-05-25

---

## Do Not Store

- daily notes
- generic journaling
- personal productivity tasks
- raw chat transcripts unless explicitly promoted into a reviewed artifact
- secrets, tokens, credentials, `.env` files
- raw customer data without a project-specific evidence policy
- build artifacts, caches, dependency directories
- large media unless the project is explicitly multimodal and evidence policy covers it
- vague "memory" summaries with no source path

---

## Do Not Automate

- autonomous rewriting of ADRs
- autonomous closure of findings
- autonomous promotion of semantic search results to decisions
- automatic vector-memory injection into implementation prompts
- broad ingestion of every file in a home directory
- Obsidian plugin workflows required for CI or runtime
- cross-project pattern creation from a single anecdote

---

## Must Remain Deterministic

- task `Context-Refs`
- retrieval manifest generation
- context packet source selection
- eval source/date validation
- ADR supersession links
- finding lifecycle status
- CI gates
- canonical artifact resolution

Semantic retrieval can suggest candidates. Deterministic links decide.

---

## Must Remain Repo-Authoritative

- implementation contract
- architecture
- task graph
- CODEX prompt state
- ADRs
- eval artifacts
- audit reports
- evidence index
- postmortems
- code and tests

If Obsidian or generated indexes disagree with these, regenerate or fix the convenience layer.

---

## Human-Reviewed Boundaries

Require human review for:

- new or superseded ADRs
- runtime tier changes
- capability profile activation or deactivation
- eval baseline resets
- closure of P1/P2 findings
- promotion of cross-project pattern notes into a project contract
- any cloud sync or semantic retrieval change that affects private data

---

## Complexity Ceilings

| Surface | Ceiling |
|---------|---------|
| Frontmatter | 5 to 10 fields for normal notes |
| Context packet | Role-scoped, normally fewer than 12 source artifacts |
| Project manifest | One file per repo |
| Cross-project pattern | Create only after reuse value is clear |
| Generated packets | Commit only major task, review, or incident packets |
| Semantic index | Optional, local or generated, never required |
| Obsidian plugins | Optional convenience only |

When a proposed memory feature needs a daemon, database, plugin dependency, or autonomous agent, treat it as out of scope until deterministic markdown retrieval proves insufficient.

