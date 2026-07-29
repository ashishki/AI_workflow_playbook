# ADR-002: Feature Design Companion JSON Registry

Date: 2026-07-29
Status: accepted

## Context

Planning Depth adds a design checkpoint before implementation for medium- and
high-risk work. The human-readable Feature Design must remain useful to
maintainers, while validators need deterministic metadata for approval and
vertical slice checks.

## Decision

Use paired artifacts:

- `docs/design/<feature-id>.md` for the human-readable Feature Design.
- `docs/design/<feature-id>.design.json` for machine-readable metadata, approval
  provenance, and vertical slice registry.

The JSON registry is validated by `schemas/feature_design.schema.json` and
consumed by `tools/playbook_validate.py`, `tools/validate_feature_design.py`,
`tools/render_slice_context.py`, and `tools/render_codex_exec_prompt.py`.

## Rationale

This avoids LLM parsing of Markdown, does not duplicate the whole design
document, keeps path/approval/slice validation deterministic, and is easy to
migrate into existing repositories. The Markdown remains authoritative for human
design discussion; the companion JSON is authoritative for readiness gates.

## Consequences

- Model self-approval is invalid. Approved design registries require human or
  authorized reviewer provenance.
- `compact_design` and `designed_slices` tasks can fail closed before
  implementation if the required registry is missing or unapproved.
- Future CLIs can map `playbook design create|validate|approve` onto the current
  thin tools without changing the artifact format.
