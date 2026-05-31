# Entropy Core Proof Layer Protocol

Status: active optional protocol
Last updated: 2026-05-31

## Purpose

Entropy Core is the optional proof layer for projects that produce claims,
reports, recommendations, agent decisions, training outcomes, or customer-facing
evidence. It does not own product runtime behavior and it is not a required
dependency for ordinary playbook adoption.

Use it to make product claims auditable:

```text
local product artifact -> evidence/receipt -> deterministic validators ->
optional Core compatibility checks -> reviewer verdict
```

## Authority

Project repositories remain authoritative. Entropy Core validates proof
contracts and blocked-surface boundaries; it does not decide product strategy,
write product reports, approve customer delivery, or replace reviews.

## Integration Levels

| Level | Name | Meaning | Use when |
|---|---|---|---|
| 0 | Reference vocabulary | Project docs use Core terms only. | Early design or paused projects. |
| 1 | Receipt-compatible | Project emits local JSON/YAML/DB receipts using Core-compatible fields. | Research briefs, weekly reports, permission decisions, source audits. |
| 2 | Core-compatible schemas | Project pins schema versions and runs schema compatibility checks. | Artifacts will evolve across phases or repos. |
| 3 | Evidence lookup compatible | Project maintains evidence refs that can be checked by Core-style lookup. | Reports cite evidence rows, source windows, or review artifacts. |
| 4 | Product bridge readiness | Core validates product adoption metadata and blocked-surface boundaries. | A product wants to rely on shared Core validators. |
| 5 | Runtime adapter | Product runtime calls Core directly. | Deferred; requires ADR and measurable value. |

Default for active products: Level 1 or Level 2. Level 4 is appropriate only
when product-local validators already exist and the project wants a stronger
cross-project proof contract.

## Proof Artifact Shape

Each product proof artifact should identify:

- artifact type and schema version;
- source project;
- task or report id;
- evidence refs;
- source artifacts and hashes where applicable;
- local validator results;
- reviewer or verifier status;
- limitations;
- blocked surfaces that are not approved.

Example:

```yaml
type: product_proof_receipt
schema_version: product-proof/v1.0.0
source_project: demand-to-mvp-radar
artifact_id: weekly-report-2026-W22
artifact_refs:
  - path: docs/reports/2026-W22.md
    sha256: "<hash>"
evidence_refs:
  - docs/EVIDENCE_INDEX.md#weekly-report-2026-W22
validators:
  - id: source_trust
    status: passed
  - id: recommendation_policy
    status: needs_more_evidence
verifier:
  method: reviewer
  status: needs_more_evidence
blocked_surfaces:
  - customer_delivery_approval
  - performance_claim
  - investment_advice
limitations:
  - "Public-source evidence only."
```

## Required Workflow

For a product task that creates or changes proof artifacts:

1. Define the product-local artifact first.
2. Add deterministic product validators.
3. Record evidence refs and hashes.
4. Decide the Entropy Core integration level.
5. If Level 2+, check schema compatibility before promoting old artifacts.
6. If Level 3+, verify evidence refs resolve to canonical project files.
7. If Level 4, add product bridge adoption metadata and blocked surfaces.
8. Review the artifact as product evidence, not as model output.

## Product Fit

Good fit:

- Telegram channel/source diligence;
- weekly market/opportunity reports;
- research brief audit receipts;
- workflow/agent blueprint receipts;
- permission training decisions;
- product bridge adoption checks;
- claim boundaries before customer-facing delivery.

Poor fit:

- UI-only polish;
- generic README updates;
- experimental brainstorming;
- runtime behavior with no auditable artifact;
- projects where proof friction is higher than risk.

## Non-Goals

Entropy Core must not become:

- a public SDK by default;
- a hosted service;
- a product report author;
- a product runtime owner;
- a customer delivery approver;
- a runtime RAG or embedding system;
- a replacement for Playbook reviews;
- a way to claim live, production, capital-ready, compliance, or performance
  approval.

## Evaluation

Track whether the proof layer reduces:

- unsupported product claims;
- missing evidence refs;
- stale schema versions;
- repeated review findings;
- customer-facing claims with no verifier status;
- time to identify why an artifact cannot be promoted.

If it only adds boilerplate without reducing those failures, keep the project at
Level 0 or Level 1.
