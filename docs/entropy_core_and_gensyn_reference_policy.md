# Entropy Core And Gensyn Reference Policy

Status: active reference policy
Last updated: 2026-05-29

## Purpose

Projects may reuse Entropy Core and Gensyn-inspired ideas, but only as portable
protocols, references, receipts, and optional validators. Do not make Entropy
Core, Gensyn, Obsidian, or any external swarm runtime mandatory for ordinary
playbook adoption.

## Entropy Core Reference Levels

| Level | Meaning | Use when |
|---|---|---|
| Reference-only | Project links to Entropy Core docs and copies no code. | Early planning and architecture docs. |
| Receipt-compatible | Project emits local YAML/JSON receipts that match shared vocabulary. | Agent actions, report claims, permission decisions, research briefs. |
| Optional validation | Project runs an Entropy Core validator manually or in CI. | High-risk workflows needing stronger evidence checks. |
| Runtime adapter | Project calls Entropy Core from runtime code. | Deferred; requires explicit ADR and measurable value. |

Default level: reference-only or receipt-compatible.

## Required Context-Refs Pattern

Tasks that use Entropy Core concepts should include scoped references:

```yaml
Context-Refs:
  - repo://Entropy_Protocol/products/entropy-core/docs/tasks.md#T123
  - repo://Entropy_Protocol/products/entropy-core/docs/tasks.md#T124
  - repo://AI_workflow_playbook/templates/RUNTIME_VERIFICATION_RECORD.md
```

The local project remains authoritative. Entropy Core references do not override
local architecture, task graph, tests, or review findings.

## Gensyn Reference Boundary

Allowed Gensyn-inspired patterns:

- diverse candidate generation;
- proposer / solver / evaluator or generator / critic / referee role split;
- contribution or action receipts;
- verification before trust;
- quality-diversity search as a design analogy.

Not adopted by default:

- decentralized training runtime;
- token incentives;
- on-chain coordination;
- P2P swarm execution;
- model weight training or RL loop;
- mandatory external Gensyn dependency.

## Attribution Template

Use this language in project docs when applying the pattern:

```md
External Reference:
- Gensyn RL Swarm, CodeZero, and DEI are design references only.
- Adapted pattern: diverse candidates + evaluator/referee verdict + evidence receipt.
- Not adopted: decentralized runtime, token incentives, model training, on-chain coordination.
```

## Code Reuse Rule

Open-source code may be inspected. Copying code requires:

- license check;
- source repository and commit reference;
- NOTICE/attribution if required;
- explicit reason not to reimplement the small local pattern;
- security review before introducing a runtime dependency.

Prefer pattern reuse over code reuse.
