# Skill Interface — External Skill Security Gate

Status: optional
Maintainer: Playbook maintainers

## Purpose

Evaluate third-party or cross-project agent skills before installation,
enablement, update, or broad sharing. This skill maps external skill supply-
chain checks into the playbook's artifact/review model without making any
specific vendor scanner mandatory.

## Trigger

- The Strategist consults this skill when the project brief proposes external
  skills, skill marketplaces, or cross-project skill reuse.
- A reviewer consults this skill when a task adds or updates files under
  `.codex/skills`, `.claude/skills`, `.cursor/`, skill registries, MCP skill
  bundles, or equivalent agent-skill directories.
- The user may invoke it explicitly before installing a skill from a Git repo,
  zip, marketplace, or vendor catalog.

## Allowed Role

| Role | Allowed |
|------|---------|
| Strategist | yes — propose trust-record tasks and approval gates |
| Orchestrator | yes — stop before installing unreviewed external skills |
| Reviewer (light or deep) | yes — verify trust records and scan evidence |
| Human | yes — approve risk acceptance and install scope |
| Codex (implementation agent) | never — Codex may implement follow-up tasks, but does not approve skills |

## Forbidden Actions

- does not install external skills
- does not execute skill scripts during review
- does not write application code
- does not modify `docs/IMPLEMENTATION_CONTRACT.md`
- does not modify `docs/ARCHITECTURE.md`, `docs/spec.md`, `docs/tasks.md`, or
  `docs/CODEX_PROMPT.md` directly
- does not bypass Phase 1 validation
- does not bypass the task graph
- does not stand in for Tool-Use, Agentic, Compliance, or runtime-tier gates
- does not treat a clean scanner report as proof that a skill is safe
- does not treat a signature as proof that a skill is safe

## Input Artifacts

- external skill source URL, release artifact, zip, directory, or `SKILL.md`
- `docs/external_skill_security_policy.md`
- `templates/EXTERNAL_SKILL_TRUST_RECORD.md`
- existing `docs/security/skills/**/TRUST_RECORD.md` records, if any
- `docs/ARCHITECTURE.md` when the skill changes capability/runtime/tool scope
- `docs/tasks.md` when follow-up implementation tasks are required

## Output Artifacts

- proposed `docs/security/skills/{skill-name}/TRUST_RECORD.md`
- proposed skill-card fields
- proposed follow-up task drafts tagged `Type: skill:security`
- proposed findings for missing scan/signature/provenance/capability evidence

The skill never writes directly to canonical artifacts without normal human or
Strategist approval.

## Evaluation Criteria

- 100% of external executable skills have trust records before installation
- 0 unresolved CRITICAL/HIGH scan findings in approved skills unless linked to
  explicit risk acceptance
- 100% of external skills are pinned by commit/hash/signature before Standard
  or Strict use
- 0 global installs without recorded human approval

## Conflict Rules

When this guide and canonical artifacts disagree, canonical wins. Default
precedence:

1. `docs/IMPLEMENTATION_CONTRACT.md`
2. `docs/adr/`
3. `docs/ARCHITECTURE.md`
4. `docs/tasks.md`
5. `docs/security/skills/**/TRUST_RECORD.md`
6. this skill guide

## Review Path

- If a skill is approved, create or update its trust record.
- If the skill adds tool, runtime, network, or data boundaries, add normal
  Codex tasks and run light/deep review.
- If the skill is rejected, record the reason in the trust record or review
  finding so it is not reintroduced silently.

## Companion Guide

`docs/external_skill_security_policy.md`
