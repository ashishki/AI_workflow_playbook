# Entropy Core And Gensyn Reference Policy

Status: active reference policy
Last updated: 2026-05-29

## Purpose

Projects may reuse Entropy Core and Gensyn-inspired ideas, but only as portable
protocols, references, receipts, and optional validators. Do not make Entropy
Core, Gensyn, Obsidian, or any external swarm runtime mandatory for ordinary
playbook adoption.

For concrete product use, treat Entropy Core as a proof layer: product-local
artifacts remain authoritative, while Core-compatible receipts, evidence refs,
schema compatibility checks, and product bridge readiness checks make claims
auditable. See `docs/entropy_core_proof_layer_protocol.md`.

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

## Gensyn Open-Source Reuse Gate

Do not reimplement a Gensyn-shaped subsystem before checking whether an official
Gensyn open-source project already solves the concrete problem.

Current official discovery sources:

- `https://github.com/gensyn-ai`
- `https://github.com/gensyn-ai/rl-swarm`
- `https://docs.gensyn.ai/testnet/rl-swarm/how-it-works`
- `https://blog.gensyn.ai/codezero-extending-rl-swarm-toward-cooperative-coding-agents/`

As of 2026-05-31, the official GitHub organization exposes relevant public
repos including `rl-swarm`, `codeassist`, `rl-swarm-contracts`, `ree`, `axl`,
and `dei`. This list is a starting point, not a frozen dependency registry;
tasks must re-check the official organization before making a reuse decision.

When a task touches any of these areas, it must run the reuse gate:

- distributed or multi-agent evaluation loops;
- proposer/solver/evaluator workflows;
- reproducible execution environments;
- P2P or encrypted agent/message routing;
- quality-diversity search;
- coding-agent training/evaluation harnesses;
- prediction-market or referee/verdict infrastructure.

Required decision order:

1. Search official Gensyn repos/docs for an existing implementation.
2. Classify each candidate as `direct_dependency`, `vendored_component`,
   `adapted_code`, `pattern_only`, or `reject`.
3. Prefer the highest-reuse option that passes fit, license, maintenance,
   security, and complexity checks.
4. If rejecting a usable Gensyn implementation, record why a local
   implementation is still better.
5. Pin any imported dependency or copied source to a repo URL, commit SHA, and
   file path.

Skipping this gate is allowed only when the task is documentation-only, the
feature is unrelated to the areas above, or the existing project docs already
contain a fresh reuse decision for the same component.

## Attribution Template

Use this language in project docs when applying the pattern:

```md
External Reference:
- Gensyn RL Swarm, CodeZero, and DEI are design references only.
- Adapted pattern: diverse candidates + evaluator/referee verdict + evidence receipt.
- Not adopted: decentralized runtime, token incentives, model training, on-chain coordination.
- OSS reuse check: official Gensyn repositories were checked before deciding
  between dependency, vendored component, adapted code, pattern-only reuse, or
  rejection.
```

## Code Reuse Rule

Open-source code should be inspected when the reuse gate applies. Copying code,
vendoring code, or adding a runtime dependency requires:

- license check;
- source repository and commit reference;
- NOTICE/attribution if required;
- explicit fit analysis against project requirements;
- explicit reason if a usable Gensyn implementation is not reused;
- security review before introducing a runtime dependency.

Prefer avoiding unnecessary dependencies for small local patterns, but do not
rebuild a non-trivial Gensyn-shaped subsystem when an official open-source
component passes the reuse gate.
