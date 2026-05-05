# Skill Interface — {{SKILL_NAME}}

A standard descriptor for optional skills layered on top of the AI Workflow Playbook.
Skills extend the workflow without modifying canonical artifacts. Every skill must
declare the fields below before it is registered in `reference/optional_skills.md`.

A skill is a constrained, opt-in capability — not a parallel control plane. The
Strategist plans, the Orchestrator drives, Codex implements, review agents review,
and the human approves phase gates. A skill never displaces those roles.

---

## Required Fields

### Status

`optional` | `experimental` | `stable`

- `experimental`: under evaluation; results recorded in `docs/research/` if present.
  Skills marked experimental can be removed without an ADR.
- `optional` / `stable`: registered in `reference/optional_skills.md`.

### Maintainer

Who owns the skill. A skill without a maintainer is not registered.

### Purpose

One paragraph. The narrow problem this skill solves and why an existing playbook
artifact does not solve it.

### Trigger

When the skill is invoked. Examples:
- by the user via a slash command
- by the Strategist during clarifying questions
- by a reviewer when a specific finding pattern appears

If the trigger is automatic, name the exact condition. Skills that fire silently
are forbidden.

### Allowed Role

Which playbook role may invoke this skill:

| Role | Allowed |
|------|---------|
| Strategist | yes / no |
| Orchestrator | yes / no |
| Reviewer (light or deep) | yes / no |
| Human | yes / no |
| Codex (implementation agent) | **never** — Codex executes tasks, not skills |

### Forbidden Actions

Every skill must include this list at minimum:

- does not write application code (no `Write` / `Edit` / `MultiEdit` to `app/`,
  `src/`, `lib/`, `tests/`); approved code changes flow through normal Codex
  tasks
- does not modify `docs/IMPLEMENTATION_CONTRACT.md`
- does not modify `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md` directly; proposes changes through normal review or
  task channels
- does not skip Phase 1 validation
- does not bypass the task graph
- does not stand in for a capability profile gate (RAG, Tool-Use, Agentic,
  Planning, Compliance)

Add skill-specific forbidden actions below this list.

### Input Artifacts

File paths the skill reads. Be specific. Globs are acceptable for scope files.

### Output Artifacts

File paths the skill writes. Outputs must be one of:

1. **Retrieval surfaces** under `docs/research/`, `docs/design/`, etc. — never
   authority over canonical files.
2. **Finding reports** under `docs/audit/` — consumed by the normal review or
   task pipeline.
3. **Proposed task drafts** that a human approves before they enter
   `docs/tasks.md`.

A skill that writes directly to canonical artifacts (architecture, contract,
spec, tasks, CODEX_PROMPT) is rejected.

### Evaluation Criteria

How a future reviewer will know the skill helped or hurt. Include at least one
numeric metric. Examples:
- review-finding count delta after skill output is consumed
- ADR revision rate after skill output is consumed
- complexity metric delta on completed phases
- clarifying-question count delta in the Strategist session

A skill without measurable criteria stays `experimental`.

### Conflict Rules

When the skill's output disagrees with a canonical document, canonical wins.
Default precedence (reuse from `IMPLEMENTATION_CONTRACT.md §Governing Documents`):

1. `docs/IMPLEMENTATION_CONTRACT.md` (highest)
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/spec.md`
5. `docs/tasks.md`
6. Skill output (lowest)

### Review Path

How the skill's output reaches the codebase. Skills NEVER apply changes
directly. Approved outputs must flow through:

- normal Codex implementation tasks (with AC, test references, commit
  granularity)
- light or deep review for any code that changes
- ADR for any architectural or contract impact

---

## Registration

A skill is registered by adding a one-line entry to `reference/optional_skills.md`
with a link to its descriptor. The descriptor lives in `templates/skills/` (this
template) or in `reference/` if it is primarily a guide rather than a reusable
template.

Removing a skill is a documentation-only change. Skills do not become canonical.
