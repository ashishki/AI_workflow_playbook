# Skill Interface — Research Companion

Status: EXPERIMENTAL — see `reference/research_companion.md` and §8
Experiment E3 in the integration assessment.
Maintainer: Playbook maintainers

## Purpose

A development-process research workflow that gives ADRs and
`docs/DECISION_LOG.md` rows better source provenance. Closes the gap where
a non-trivial technology, compliance, or runtime decision currently relies
on Strategist judgment without an evidence trail. Different from the RAG
capability profile, which governs application-runtime retrieval.

## Trigger

- The Strategist invokes the skill when an architectural choice has more
  than one defensible answer and the team will be asked "why this choice"
  later.
- A reviewer invokes the skill when flagging a decision as under-justified
  during deep review (META or ARCH).
- The user invokes it explicitly when drafting a high-stakes ADR.

Skills NEVER fire automatically. The trigger is always an explicit human or
reviewer action.

## Allowed Role

| Role | Allowed |
|------|---------|
| Strategist | yes |
| Orchestrator | no |
| Reviewer (light or deep) | yes — to request evidence before closing a finding |
| Human | yes |
| Codex (implementation agent) | never |

## Forbidden Actions

- does not write application code
- does not modify `docs/IMPLEMENTATION_CONTRACT.md`,
  `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md` directly
- does not skip Phase 1 validation
- does not bypass the task graph
- does not stand in for code-level evidence (tests, evaluation artifacts,
  review findings)
- does not replace an ADR — research notes are read by ADRs, not the other
  way around

## Input Artifacts

- a research question with scope and deadline
- the consuming artifact (ADR-NNN draft or `docs/DECISION_LOG.md` row)
- existing canonical documents that constrain the answer
  (`docs/ARCHITECTURE.md`, `docs/IMPLEMENTATION_CONTRACT.md`, prior ADRs)

## Output Artifacts

- `docs/research/{topic-slug}.md` produced from
  `templates/research/RESEARCH_NOTE.md`
- the consuming ADR or `docs/DECISION_LOG.md` row cites the note via
  `(research: docs/research/{slug}.md#R-N)`

The skill never writes directly to canonical artifacts.

## Evaluation Criteria

Per §8 Experiment E3:

- ADR revision rate: ≥1 fewer revision on average for ADRs that consume a
  research note vs. ADRs of similar scope without one
- review findings citing rationale gaps: zero on research-backed ADRs
  within the next two phases
- days from ADR draft to acceptance: not increased materially

If results do not show measurable value, the skill is removed. If they do,
the skill is promoted to `Status: optional` per the promotion path in
`reference/research_companion.md`.

## Conflict Rules

Default precedence (lowest priority for skill output):

1. `docs/IMPLEMENTATION_CONTRACT.md` (highest)
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/spec.md`
5. `docs/tasks.md`
6. Skill output (`docs/research/{slug}.md`) — lowest

When evidence in a research note materially conflicts with a canonical
document, the path is: file an ADR; only then update the canonical
document. The research note is updated to record the resolution.

## Review Path

- Research notes are read by the human, the Strategist, or a reviewer
  before they cite the note in a canonical document.
- A review finding cannot be closed solely because the research note says
  the issue is fine — code-level evidence is still required.
- Removing or invalidating a research note does not require an ADR; it is
  a documentation-only change.

## Companion Guide

`reference/research_companion.md`
