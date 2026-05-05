# Skill Interface — External Tools / MCP

Status: optional
Maintainer: Playbook maintainers

## Purpose

Wire external tool integrations — MCP servers, REST APIs, vendor SDKs — into
the existing Tool-Use profile without making any vendor mandatory and without
introducing a new capability profile. Closes the documentation gap where a
project activates Tool-Use=ON but has no worked example for catalog rows,
unsafe-action shape, secret handling, audit log fields, schema versioning,
and rollback policy.

## Trigger

- The Strategist consults this skill when Tool-Use Profile = ON and at least
  one tool reaches an external service through an MCP server or equivalent
  shape.
- A reviewer consults this skill when reviewing TOOL-1 / TOOL-2 / TOOL-6
  findings on MCP-backed tools.
- The user may invoke it explicitly when adding a new MCP integration mid-
  project.

## Allowed Role

| Role | Allowed |
|------|---------|
| Strategist | yes — propose Tool Catalog rows during Phase 1 |
| Orchestrator | no — orchestrator does not design tools |
| Reviewer (light or deep) | yes — verify Tool Catalog rows match the guide |
| Human | yes — author Tool Catalog entries when adding integrations |
| Codex (implementation agent) | never — Codex implements the tools, not the catalog design |

## Forbidden Actions

- does not write application code; tool implementations flow through normal
  Codex tasks tagged `Type: tool:schema`, `tool:unsafe`, or `tool:call`
- does not modify `docs/IMPLEMENTATION_CONTRACT.md`
- does not modify `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md` directly; proposes Tool Catalog rows for the human
  or Strategist to insert
- does not skip Phase 1 validation
- does not bypass the task graph
- does not stand in for the Tool-Use profile gate — TOOL-1..6 still fire
- does not mandate any specific MCP vendor; the guide is shape-only

## Input Artifacts

- `docs/ARCHITECTURE.md §Capability Profiles` (must declare Tool-Use = ON)
- `docs/ARCHITECTURE.md §Tool Catalog` (current rows, if any)
- `docs/ARCHITECTURE.md §Runtime Contract` (env vars)
- `templates/IMPLEMENTATION_CONTRACT.md §Profile Rules: Tool-Use`
- `prompts/audit/PROMPT_2_CODE.md` TOOL-1..6
- the MCP server's published tool list and version

## Output Artifacts

- proposed Tool Catalog rows (text fragments) — the human inserts them
- proposed env-var entries for `docs/ARCHITECTURE.md §Runtime Contract`
- audit-log shape note for the project's observability section
- proposed task drafts (`tool:schema` / `tool:unsafe`) for `docs/tasks.md`,
  reviewed before insertion

The skill never writes directly to canonical artifacts.

## Evaluation Criteria

- on projects using the guide: zero TOOL-1 findings (missing catalog rows) at
  the first deep review after MCP integration
- zero credential-mount findings
- 100% of `destructive` tools have a distinct confirmation code path verified
  by `TOOL-L1` light review
- if used in repeated projects: regression in any of the above is a signal to
  revise the guide, not the project

## Conflict Rules

When the guide and a canonical artifact disagree, canonical wins. Default
precedence:

1. `docs/IMPLEMENTATION_CONTRACT.md §Profile Rules: Tool-Use` (highest)
2. `docs/adr/`
3. `docs/ARCHITECTURE.md §Tool Catalog` once filled
4. This guide (lowest, advisory only)

## Review Path

- Tool Catalog rows proposed by this skill enter `docs/ARCHITECTURE.md` only
  via normal architectural updates (Strategist or human edit; ADR if the
  change crosses a boundary).
- Tool implementations enter the codebase only via Codex tasks. Light review
  fires `TOOL-L1` for `tool:unsafe`. Deep review fires `TOOL-1..6`.

## Companion Guide

`reference/external_tools_mcp_companion.md`
