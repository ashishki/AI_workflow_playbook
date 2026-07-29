# Feature Design

## Metadata

Feature-ID:
Status: draft
Planning-Depth:
Owner:
Risk-Level:
Related-Tasks:
Brief-Ref: docs/PROJECT_BRIEF.md
Architecture-Refs:
Created-At: {{DATE}}
Approved-By:
Approved-At:

Allowed statuses: `draft`, `review_required`, `approved`, `superseded`,
`rejected`, `implemented`.

Do not mark this design `approved` yourself. Approval requires human or
authorized-reviewer provenance in the companion `.design.json` registry.

## 1. Product Outcome

- Concrete user or operational problem:
- Expected outcome:
- First proof metric:
- Non-goals:
- Observable user touchpoint:

## 2. Existing System Context

- Existing components and patterns to reuse:
- Authoritative architecture/contracts:
- Relevant prior decisions:
- Existing interfaces:
- Constraints:

## 3. System Impact

- Components:
- APIs:
- Data flow:
- Persistence:
- Queues/jobs:
- Permissions:
- Privacy/security boundaries:
- External dependencies:
- Migration implications:

## 4. Program Design

### File Tree Diff

```text
M app/api/routes.py
M app/services/corrections.py
A app/models/correction.py
A tests/test_correction_flow.py
```

### Key Types

```text
CorrectionRecord
CorrectionStatus
ApprovalDecision
```

### Interfaces And Signatures

Use pseudocode or signatures. Do not include full implementation.

```text
CorrectionService.create(input: CorrectionInput) -> CorrectionRecord
```

### Control Flow / Call Stack

```text
POST /corrections
+-- CorrectionService.create()
    +-- validate_input()
    +-- repository.save()
    +-- event_bus.publish()
```

### Invariants

- 

### Failure Paths

- 

### Patterns To Reuse

- 

### Patterns Not To Introduce

- 

### Rollback / Recovery

- 

## 5. Maintainability Risks

- New abstractions:
- Coupling:
- Duplicate domain logic:
- Shotgun surgery risk:
- Dependency expansion:
- Migration burden:
- Hidden global state:
- Bypass of type system:
- Future extension pressure:

## 6. Verification Strategy

- Unit tests:
- Integration tests:
- Project verifier:
- Capability evals:
- Holdout/critic requirements:
- User-visible demo or smoke path:

## 7. Vertical Slices

For `designed_slices`, each slice must pass through the necessary layers and
produce a small verified user-visible outcome. Avoid purely horizontal split
plans where all models, then all services, then all endpoints, then all UI are
implemented before any outcome can be checked.

```text
Slice-ID:
Status: planned
User-Visible Outcome:
Scope:
Allowed-Files:
Forbidden-Files:
Expected Interfaces:
Verification:
Review-Checkpoint:
Dependencies:
Change-Budget:
Rollback:
```

## 8. Open Decisions

- 

## 9. Human Approval

- Approval policy:
- Required approver:
- Approval artifact/ref:
- Notes:

The model may draft, compare alternatives, and update this design from feedback.
The model may not approve its own design or assign release readiness.
