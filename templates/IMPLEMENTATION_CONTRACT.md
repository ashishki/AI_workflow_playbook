# Implementation Contract — {{PROJECT_NAME}}

Status: **IMMUTABLE** — changes to this document require an Architectural Decision Record filed in `docs/adr/`.
Version: 1.0
Effective date: {{DATE}}

Any agent (Codex or review) may cite this document as the authority on implementation rules. Any finding that this contract was violated is automatically P1.

---

## Universal Rules

These rules apply to every project using the AI Workflow Playbook. They are not negotiable and are not changed without an ADR.

### SQL Safety

- All SQL is parameterized. Use `text()` with named parameters: `text("SELECT ... WHERE id = :id")` with `{"id": value}`.
- Never interpolate variables into SQL strings. This includes f-strings, `%` formatting, and `+` concatenation.
- Never use string concatenation to build any part of a query, including table names, column names, or `ORDER BY` clauses.
- Violation: automatic P1.

### Multi-Tenant Systems

_Applies only if {{PROJECT_NAME}} is multi-tenant. Delete this section if single-tenant._

- Every database call that touches tenant-scoped tables must be preceded by the tenant context: `SET LOCAL app.tenant_id = :tid`.
- No query executes against tenant-scoped tables without a tenant context.
- Session-level `SET` (without `LOCAL`) is forbidden in multi-tenant code paths — it leaks tenant context across requests.
- RLS policies in migrations enforce the above at the database layer as a second line of defense.
- Violation: automatic P1.

### Async Redis

- Redis is accessed only in `async def` functions.
- Use `redis.asyncio`, not the synchronous `redis` client.
- Never call synchronous Redis methods from async code paths (no `asyncio.get_event_loop().run_in_executor()` workarounds).
- Violation: automatic P1.

### Authorization

- Every new route handler enforces authorization before accessing any data.
- Authorization means: verify the caller is who they claim to be (authentication) AND verify they are allowed to do what they are requesting (authorization).
- "We'll add auth later" is not an acceptable deferral. If a route is intentionally public, document it explicitly in the route handler with a comment citing the design decision.
- Violation: automatic P1.

### PII Policy

- No PII in log messages (`logger.info`, `logger.warning`, `logger.error`, etc.).
- No PII in span attributes (OpenTelemetry or any other tracing system).
- No PII in metrics labels or metric values.
- No PII in error messages returned to clients.
- Where identifiers must appear in observability data, use SHA-256 hashes.
- Fields considered PII in this project: {{LIST_PII_FIELDS}}
- Violation: automatic P1.

### Credentials and Secrets

- No credentials, API keys, tokens, passwords, or secrets in source code.
- No credentials in comments.
- No credentials in test fixtures (use test-key or equivalent placeholder strings in tests; real values come from environment variables).
- All secrets come from environment variables. Document required env vars in `docs/ARCHITECTURE.md` under Runtime Contract.
- `.env` files are in `.gitignore` and are never committed.
- Violation: automatic P1 (and a security incident).

### Shared Tracing Module

- One shared tracing module: `{{TRACING_MODULE_PATH}}` with a single `get_tracer()` function.
- All code that creates spans imports from this module.
- No inline noop span implementations in individual files.
- No copy-pasted tracer initialization in individual modules.
- Violation: P2 (accumulates; becomes P1 at age cap).

### CI Gate

- CI must pass before any PR is merged.
- A PR with failing CI is never merged, regardless of deadline pressure.
- If CI is flaky (non-deterministic failures), the flakiness is fixed before the PR is merged — not bypassed.
- Violation: automatic P1.

---

## Project-Specific Rules

_The following rules are tailored to {{PROJECT_NAME}} based on its stack and constraints. They carry the same weight as the universal rules above._

### {{PROJECT_SPECIFIC_RULE_1}}

{{DESCRIPTION_AND_RATIONALE}}

Violation: {{SEVERITY}}

### {{PROJECT_SPECIFIC_RULE_2}}

{{DESCRIPTION_AND_RATIONALE}}

Violation: {{SEVERITY}}

<!--
Examples of project-specific rules:
- "All background tasks must be idempotent — the task queue may deliver a task more than once."
- "API responses must not include internal database IDs — use UUIDs exposed through the API."
- "All file uploads must be scanned before being stored — never store an unscanned file."
- "Rate limiting is enforced at the route level for all public-facing endpoints."
-->

---

## Profile Rules: RAG

<!--
This section applies ONLY when RAG Status = ON in the ## Capability Profiles table
in docs/ARCHITECTURE.md. If RAG Status = OFF, delete this entire section.
-->

_Applies only when `docs/ARCHITECTURE.md` declares RAG Status = ON in the Capability Profiles table._

### Corpus Isolation

- Every retrieval query must be scoped to the corpus the caller is authorized to access.
- Cross-corpus retrieval (e.g., querying another tenant's documents) is treated as a data leak — automatic P1.
- Corpus boundaries are enforced at the retrieval layer (namespace filter, metadata filter, or separate index), not only at the application layer.

### insufficient_evidence Path

- Every query-time handler must implement the `insufficient_evidence` path.
- When retrieved evidence does not meet the minimum confidence or coverage threshold, the system must return `insufficient_evidence` — not a hallucinated answer.
- This path must have at least one explicit test in the integration test suite.
- Omitting this path is an automatic P1.

### Index Schema Versioning

- The index schema (embedding model, chunking strategy, metadata fields) is versioned.
- Changing any schema parameter requires an ADR. After the ADR is filed, the corpus must be fully re-indexed before the new schema goes to production.
- A partial index (some documents using old schema, some using new) is forbidden.

### Max Index Age

- The maximum allowed age for indexed documents is: `{{MAX_INDEX_AGE, e.g., "24 hours"}}`.
- The health endpoint must expose index freshness. A stale index beyond this threshold must produce a non-200 response or an explicit staleness warning.
- Violation: P2 (escalates to P1 if index age exceeds 2× the max threshold).

### Retrieval-Generation Separation

- Ingestion pipeline code and query-time retrieval code live in separate modules.
- A single function or class must not mix ingestion logic (extract, chunk, embed, index) with query-time logic (retrieve, rerank, assemble).
- Violation: P2.

### RAG P2 Age Cap Override

For retrieval-critical findings (corpus isolation, `insufficient_evidence` path, schema drift), the standard P2 Age Cap of 3 cycles is reduced to **1 cycle**. A retrieval P2 that is not resolved after 1 review cycle is automatically escalated to P1.

### Retrieval Evaluation Gate

A retrieval-related task (tagged `Type: rag:ingestion` or `Type: rag:query`, or touching chunking, embedding, ranking, evidence assembly, or `insufficient_evidence` behavior) is **not complete** unless all three of the following are true:

1. `docs/retrieval_eval.md` is updated with current metrics for the affected pipeline stage.
2. Current metrics are explicitly compared to the baseline row in the Evaluation History table.
3. Any metric regressions are documented in the Regression Notes section with a justification.

Submitting a task as `IMPLEMENTATION_RESULT: DONE` without fulfilling these conditions is a P1 finding. The code passing tests does not imply the retrieval is correct.

### Retrieval Regression Policy

A retrieval regression (any metric decline vs. the current baseline) is a **P1 finding** unless:
- the regression is documented in `docs/retrieval_eval.md §Regression Notes`
- a trade-off justification is provided (e.g., latency increased because reranking was added and quality improved)
- the human reviewer explicitly accepts it before the phase gate passes

"Tests are green" does not close a retrieval regression.

---

## Profile Rules: Tool-Use

<!--
This section applies ONLY when Tool-Use Status = ON in docs/ARCHITECTURE.md.
If Tool-Use Status = OFF, delete this entire section.
-->

_Applies only when `docs/ARCHITECTURE.md` declares Tool-Use Status = ON._

### Tool Schema Versioning

- Every tool schema is versioned. A schema change requires a task entry in `docs/tasks.md` and a test that validates the new schema at generation time.
- Callers must not depend on undocumented fields — the schema is the contract.

### Unsafe-Action Confirmation

- Every tool classified as destructive or irreversible in ARCHITECTURE.md §Tool Catalog requires an explicit confirmation step before execution.
- The confirmation step must be a distinct code path — not a flag, not a comment.
- Violation: automatic P1.

### Side-Effect Documentation

- Every tool that writes, modifies, or deletes external state must document its side effects in ARCHITECTURE.md §Tool Catalog.
- A tool that produces undocumented side effects is a P1 finding.

### Idempotency

- Tools classified as write or destructive must be idempotent where technically feasible.
- Non-idempotent writes must be explicitly marked as such in ARCHITECTURE.md §Tool Catalog with the reasoning.

---

## Profile Rules: Agentic

<!--
This section applies ONLY when Agentic Status = ON in docs/ARCHITECTURE.md.
If Agentic Status = OFF, delete this entire section.
-->

_Applies only when `docs/ARCHITECTURE.md` declares Agentic Status = ON._

### Loop Termination Contract

- The loop termination contract (max iterations, termination conditions, forced-termination behavior) defined in ARCHITECTURE.md §Loop Termination Contract is immutable. Changing it requires an ADR.
- An agent loop without an explicit termination contract is a P0 finding.

### Authority Boundary Enforcement

- Each agent role must operate within the authority scope defined in ARCHITECTURE.md §Agent Roles.
- No agent role may initiate actions outside its declared authority scope without an explicit handoff.
- Cross-role authority escalation without a handoff is a P1 finding.

### Cross-Iteration State Management

- State that persists across loop iterations must follow the state schema defined in ARCHITECTURE.md §Agent Handoff Protocol.
- Mutating shared state without a schema is a P1 finding.
- Tests must cover the case where the loop resumes from an intermediate state (not only clean-start).

### Handoff Integrity

- Every handoff between agent roles must produce a structured output the receiving role can validate.
- A handoff that silently drops required fields is a P1 finding.

---

## Profile Rules: Planning

<!--
This section applies ONLY when Planning Status = ON in docs/ARCHITECTURE.md.
If Planning Status = OFF, delete this entire section.
-->

_Applies only when `docs/ARCHITECTURE.md` declares Planning Status = ON._

### Plan Schema Versioning

- The plan schema (ARCHITECTURE.md §Plan Schema) is versioned. Changing the schema requires an ADR and a migration plan for any downstream consumers.

### Validation Gate

- Every plan generated by the system must pass schema validation before leaving the system boundary (API response, file write, or handoff to another system).
- A plan that bypasses the validation gate is a P0 finding.
- Tests must cover invalid plan rejection — not only valid plan acceptance.

### Plan-to-Execution Contract Immutability

- The plan-to-execution contract defined in ARCHITECTURE.md §Plan-to-Execution Contract is immutable without an ADR. Downstream consumers depend on it.

### Replan Boundaries

- Replan triggers are declared in ARCHITECTURE.md §Plan Validation. The system must not replan outside those declared triggers without explicit human approval.
- Unbounded replanning is equivalent to an unbounded agent loop: apply the same termination contract.

---

## Mandatory Pre-Task Protocol

Every Codex agent must execute these steps before writing any implementation code. No exceptions.

1. Read `docs/IMPLEMENTATION_CONTRACT.md` (this file) from top to bottom.
2. Read the full task in `docs/tasks.md`, including all acceptance criteria, the Depends-On list, and the Notes section.
3. Read all Depends-On tasks to understand the interface contracts your implementation must satisfy.
4. Run `pytest -q`. Record the output: `{N} passing, {M} failed`. If M > 0, stop and report — you do not start on a broken baseline.
5. Run `ruff check`. Must exit 0. If not, create a separate commit with ruff fixes, then restart the pre-task protocol.
6. Confirm that every acceptance criterion in the task will have a corresponding test before implementation is considered complete.

Skipping any step in this protocol is a P1 finding in the next review cycle.

---

## Forbidden Actions

The following actions are never permitted. Violating these generates a P1 finding in the next review cycle.

| Forbidden Action | Reason |
|-----------------|--------|
| String interpolation in SQL (`f"SELECT * FROM t WHERE id = {id}"`) | SQL injection; parameterized queries are unconditional |
| Session-level `SET` in multi-tenant code paths | Leaks tenant context across requests |
| Skipping the pre-task baseline capture | Cannot verify implementation did not break existing tests |
| Self-closing a review finding without showing the code change | Findings are verified by reading code, not by assertion |
| Modifying this document without an ADR | The contract is immutable by design |
| Deferring CI setup past Phase 1 | Every commit must be CI-verified |
| Merging a PR with failing CI | The CI gate is non-negotiable |
| Committing credentials or secrets of any kind | Irreversible exposure |
| Leaving commented-out code in a commit | Dead code degrades readability; delete it |
| Adding a TODO without a task reference | Orphaned TODOs accumulate and are never addressed |

---

## Quality Process Rules

### P2 Age Cap

Any P2 finding that remains open for more than 3 consecutive review cycles must be:
- Closed (resolved with a code change and a passing test), OR
- Escalated to P1 (and resolved before the next phase gate), OR
- Formally deferred to v2 (with an ADR filed in `docs/adr/`, removing it from open findings)

A P2 finding cannot be silently aged out. The Age Cap rule prevents the finding backlog from becoming a graveyard.

### Commit Granularity

One logical change per commit. If a task involves a database migration, a service implementation, and tests, that is at minimum three commits. Never bundle unrelated changes in a single commit. "Misc fixes" is not a commit message.

### Sandbox Isolation

Tests do not share state. Each test that touches the database uses a transaction that is rolled back at the end of the test (or uses a fresh database per test run). Tests that share mutable state produce non-deterministic results and are treated as broken tests.

### Review Cycle Integrity

Review agents close findings only after verifying the fix in code. A finding is not closed because the Codex agent claims it was fixed. It is closed because a review agent read the relevant code and confirmed the fix is present and correct.

---

## Governing Documents

| Document | Path | Role |
|----------|------|------|
| Architecture | `docs/ARCHITECTURE.md` | System design authority — what the system is and why |
| Specification | `docs/spec.md` | Feature authority — what the system does |
| Task graph | `docs/tasks.md` | Implementation authority — what each agent builds |
| Session handoff | `docs/CODEX_PROMPT.md` | State authority — current baseline, open findings, next task |
| This document | `docs/IMPLEMENTATION_CONTRACT.md` | Rule authority — immutable implementation rules |
| Review reports | `docs/audit/CYCLE{N}_REVIEW.md` | Finding authority — official record of review cycles |
| ADRs | `docs/adr/ADR{NNN}.md` | Decision authority — architectural decisions and their rationale |
| Dev standards | `docs/dev-standards.md` | Style authority — code style, test strategy, observability conventions |

In case of conflict between documents, the precedence order is:
1. This document (IMPLEMENTATION_CONTRACT.md) — highest authority for rules
2. docs/adr/ — overrides architecture and spec when a formal decision was made
3. docs/ARCHITECTURE.md — overrides spec for technical design
4. docs/spec.md — overrides tasks for feature scope
5. docs/tasks.md — overrides CODEX_PROMPT for task-level details
