# README-First Knowledge Index

Status: active protocol
Last updated: 2026-06-08

## Purpose

README-first knowledge indexes give humans and agents a cheap local map of a
repo, folder, service, product workspace, or subsystem.

The rule is simple: when a phase changes an important boundary, the nearest
`README.md` index must point to the canonical artifacts that explain the new
state.

This is not a new memory layer. It is a navigation discipline.

## Authority Rule

`README.md` files are indexes, not authority.

They may summarize current status, decisions, constraints, patterns, and known
gaps, but every material claim must link to canonical artifacts:

- `docs/ARCHITECTURE.md`
- `docs/IMPLEMENTATION_CONTRACT.md`
- `docs/tasks.md`
- `docs/CODEX_PROMPT.md`
- `docs/DECISION_LOG.md`
- `docs/adr/`
- eval artifacts
- `docs/EVIDENCE_INDEX.md`
- runtime verification records
- proof receipts
- review reports

If a README conflicts with a canonical artifact, the canonical artifact wins.

## When Required

Update the nearest README index before a phase gate when the phase changed any
of these:

- architecture or runtime boundaries;
- product or service workflow;
- public API, CLI, export, or report surface;
- task ownership or active roadmap;
- evidence, eval, receipt, or review surface;
- provider/tool/runtime policy;
- privacy, compliance, or human approval boundary;
- major folder/module responsibility.

If the phase only changed narrow implementation details inside an already
documented boundary, a README update may be skipped. The phase report should
state why it was not needed.

## README Shape

Use this lightweight shape for repo, `docs/`, product, service, or subsystem
indexes:

```markdown
# <Area Name>

Status: <active | paused | archived | experimental>

## Purpose

One paragraph: what this area is responsible for.

## Start Here

- `<canonical file>` - why it matters
- `<canonical file>` - why it matters

## Current State

- Current active behavior or phase.
- What is deliberately not included.

## Key Decisions

- `<ADR or decision log ref>` - one-line decision.

## Contracts, Proof, and Evals

- `<contract/eval/receipt/review ref>` - what it verifies.

## Active Tasks

- `<task ref>` - next implementation or review step.

## Known Gaps

- Gap and where it is tracked.
```

Keep it short. A README index should route the reader, not duplicate the docs it
links to.

## Phase-Gate Check

Before closing a phase:

1. Identify folders/workspaces whose boundaries changed.
2. Open the nearest `README.md` for each changed area.
3. Update links, status, active tasks, key decisions, proof/eval references, and
   known gaps.
4. If no README exists and the area is now substantial, create one using
   `templates/README_INDEX.md`.
5. Record the update or justified omission in the phase summary.

## Relationship To Cognition Vault

README-first indexes are the first local navigation layer.

Recommended order for cold starts:

1. repo or folder `README.md`
2. `docs/CODEX_PROMPT.md`
3. `docs/PROJECT_PLAN.md` or `docs/tasks.md`
4. canonical docs and Context-Refs
5. `docs/COGNITION_MANIFEST.md`
6. external cognition vault or generated context packets

The cognition vault remains useful for portfolio and cross-project context.
README indexes keep the local repo navigable without requiring Obsidian, a
plugin, a generated graph, or a memory runtime.

## Optional Tooling

Markdown search, README graph maps, broken-link checks, and ontology-style lint
tools are allowed as optional helpers. They must remain derived from committed
markdown and must not become mandatory runtime dependencies.
