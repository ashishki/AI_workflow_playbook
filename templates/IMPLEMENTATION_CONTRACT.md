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
