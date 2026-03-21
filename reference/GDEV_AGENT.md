# Reference Implementation: gdev-agent

Repository: https://github.com/ashishki/gdev-agent

---

## What gdev-agent Is

gdev-agent is a multi-tenant AI triage service built using the AI Workflow Playbook over 12 phases. It is a real production-grade codebase, not a toy example. It demonstrates what this playbook looks like applied end-to-end.

**Stack:** FastAPI, PostgreSQL 16 with pgvector, Redis 7, Claude API (Anthropic), OpenTelemetry, SQLAlchemy 2.x, pytest.

**Architecture:** Multi-tenant SaaS service. Tenants are isolated via PostgreSQL Row-Level Security. Each request carries a tenant context set via `SET LOCAL`. Embeddings are stored in pgvector for vector similarity search. Auth is JWT + Redis-based blocklist. Observability via OpenTelemetry with a shared tracing module.

**Development process:** 12 phases. Each phase closed with a full META → ARCH → CODE → CONSOLIDATED review cycle. `docs/audit/` contains the actual review cycle reports. `docs/CODEX_PROMPT.md` shows what the session handoff document looks like mid-project.

gdev-agent is the **reference**, not the template. Adapt its patterns to your stack. If your project is single-tenant, ignore the RLS setup. If your project does not use pgvector, ignore the embedding patterns. Use the structure and the discipline, not the specifics.

---

## When to Reference It

**Strategist agent:** When you are uncertain how to structure a document (ARCHITECTURE.md, tasks.md, CODEX_PROMPT.md), look at how gdev-agent structures the equivalent document. The gdev-agent docs are the canonical format example.

**Codex agent:** When you need a concrete example of a pattern (service layer, shared tracing, parameterized SQL, test fixtures), read the corresponding file in gdev-agent before implementing your own version. Do not reinvent the wheel — understand the pattern and adapt it.

**Orchestrator:** When you are uncertain what a review cycle report should look like, read `docs/audit/` in gdev-agent. When you are uncertain what a mature CODEX_PROMPT.md looks like, read gdev-agent's.

---

## Key Patterns — What to Study and Why

### Service Layer Pattern

**Where:** `app/services/` directory, `app/main.py` or `app/routers/`

**Pattern:** Route handlers are thin. They extract validated parameters from the request and immediately delegate to a service function. The service function contains all business logic and accepts only primitives and database sessions — no HTTP objects (no `Request`, no `Response`).

**Why this matters:** Services that accept primitives are testable without running an HTTP server. You can call a service function directly in a unit test, pass it fake data and a database session, and verify its behavior. This is the primary reason the service layer pattern exists.

**What to look for:** A route handler that does nothing but validate input, call a service, and return the result. A service function that has no `import fastapi` at the top of its file.

**Adaptation note:** The pattern works regardless of framework. If you're using Django, the view is thin and the "service" might be a class in `services.py`. If you're using Flask, the route function delegates to a service module. The principle is framework-agnostic.

---

### Shared Tracing Module

**Where:** `app/tracing.py`

**Pattern:** One file exports one function: `get_tracer()`. Every file that creates spans imports this function. There are no inline tracer initializations scattered across the codebase.

**Why this matters:** Without a shared tracing module, tracing setup duplicates across files. Each file might initialize its own tracer with slightly different configuration. Span naming becomes inconsistent. When you need to change the tracing backend or configuration, you have to find and update every file.

**What to look for:** `from app.tracing import get_tracer` at the top of files that create spans. A single `tracing.py` file that configures the tracer once and exports it.

**Adaptation note:** The specific tracing library (OpenTelemetry, Datadog, etc.) doesn't matter. The pattern is: one initialization, one import, consistent configuration everywhere.

---

### Multi-Tenant Row-Level Security

**Where:** `app/db.py`, `alembic/versions/` (migration files)

**Pattern:** PostgreSQL RLS policies are defined in migration files. Before every query, the application executes `SET LOCAL app.tenant_id = :tid` within the transaction. RLS policies on tenant-scoped tables enforce that `current_setting('app.tenant_id')` matches the `tenant_id` column.

**Why this matters:** Application-layer tenant filtering is a second line of defense. It can be bypassed by a bug — a missing `.filter(tenant_id=tid)` on one query path exposes all tenants' data. Database-layer RLS cannot be bypassed by application bugs — if the tenant context is not set, the query returns no rows (or raises an error, depending on the policy).

**What to look for:** Migration files that `CREATE POLICY` on tenant-scoped tables. A function in `db.py` that wraps every session with `SET LOCAL`. Every service function that accepts a `tenant_id` parameter and passes it to the session setup.

**Adaptation note:** Skip this section entirely if your project is single-tenant. Multi-tenancy adds significant complexity and is only warranted when the spec requires it.

---

### Authentication — JWT + Redis Blocklist

**Where:** `app/middleware/auth.py`, `app/services/auth_service.py`

**Pattern:** JWT tokens are validated in middleware. Middleware extracts the token from the `Authorization: Bearer` header, verifies the signature and expiry, and checks the token's JTI (JWT ID) against a Redis blocklist. If the JTI is in the blocklist, the token is rejected even if the signature is valid. On logout, the JTI is added to Redis with TTL = remaining token lifetime.

**Why this matters:** JWTs are stateless by design — a valid token cannot be invalidated without a blocklist. The Redis blocklist provides the equivalent of session revocation for stateless auth.

**What to look for:** `app/middleware/auth.py` — middleware that runs before route handlers. `app/services/auth_service.py` — token creation, validation, and revocation logic. Redis client usage in `async def` functions only.

**Adaptation note:** If your project uses API keys instead of JWTs, the blocklist pattern still applies (blocklist API keys in Redis when revoked). If your project uses OAuth2, the token validation changes but the middleware pattern stays the same.

---

### Test Structure

**Where:** `tests/conftest.py`, `tests/test_*.py` or `tests/unit/`, `tests/integration/`

**Pattern:** `conftest.py` defines fixtures for the database session (with transaction rollback after each test), the HTTP test client, and mock external services. Unit tests call service functions directly with a real or fake database session. Integration tests call route handlers via the HTTP test client. Tests do not share mutable state.

**Why this matters:** Fixtures defined in `conftest.py` are reusable across all test files without import. Transaction rollback after each test ensures tests are isolated — state from one test never affects another. Separating unit tests (fast, no I/O) from integration tests (slower, full stack) allows running the fast suite in tight loops during development.

**What to look for:** A `db_session` fixture in `conftest.py` that uses `BEGIN` + `ROLLBACK` to isolate each test. A `client` fixture that creates a `TestClient` or `AsyncClient` with the app. Fixtures that yield (not return), so cleanup runs even if the test fails.

**Adaptation note:** The transaction-rollback isolation pattern works with any SQL database. For MongoDB or other non-relational databases, the equivalent is dropping and recreating a test database for each test run, or using a test container that resets between tests.

---

### CODEX_PROMPT.md Format — Mid-Project Example

**Where:** `docs/CODEX_PROMPT.md`

Reading gdev-agent's `CODEX_PROMPT.md` at a mid-project phase (e.g., Phase 6) is more instructive than reading a template. It shows:
- What the "Current State" section looks like with a real baseline (not 0 tests)
- What the "Open Findings" section looks like with actual P2 findings from a previous cycle
- What the "Fix Queue" looks like when it has real deferred items
- How "Completed Tasks" accumulates over time

The template in `templates/CODEX_PROMPT.md` in this playbook shows the structure. gdev-agent's actual file shows what a lived-in version looks like.

---

### Review Cycle Reports

**Where:** `docs/audit/CYCLE{N}_REVIEW.md`

Reading two or three review cycle reports from gdev-agent is more instructive than reading a description of what they contain. The reports show:
- The actual severity and specificity of P1/P2/P3 findings
- How findings reference specific files and line numbers
- How PROMPT_4 (CONSOLIDATED) merges and deduplicates
- How the gate decision is stated ("Phase gate: OPEN" or "Phase gate: BLOCKED — resolve P1-03 first")
- How findings from previous cycles are tracked (P2 age tracking)

---

### CI Configuration

**Where:** `.github/workflows/ci.yml`

The gdev-agent CI file is a working example with PostgreSQL/pgvector and Redis services. It is the proven pattern that the `ci/ci.yml` template in this playbook is based on. If the template's service block configuration is unclear, read the gdev-agent version — it has the exact health check syntax, port mapping, and env var setup that works.

---

## What NOT to Copy from gdev-agent

gdev-agent is opinionated about its specific domain. Do not copy:

- **Multi-tenancy setup** if your project is single-tenant. The RLS policies, tenant context middleware, and per-request `SET LOCAL` add real complexity and are only justified when the spec requires multi-tenancy.

- **pgvector / embedding patterns** if your project does not do vector similarity search. This is gdev-agent's domain-specific feature, not a universal pattern.

- **The specific Claude API integration** unless your project also calls Claude. The pattern for calling an external AI API is generalizable; the specific prompt structure and model selection are not.

- **Domain-specific data models** — gdev-agent's models are for its specific domain (triage tickets, tenants, etc.). Your models will be different.

The patterns to reuse are structural (service layer, shared tracing, test fixtures, CODEX_PROMPT format, review cycle format). The domain specifics do not transfer.

---

## Quick Reference — File Map

| Pattern | File in gdev-agent | What to read for |
|---------|--------------------|-----------------|
| Service layer | `app/services/*.py`, `app/routers/*.py` | How thin handlers delegate to services |
| Shared tracing | `app/tracing.py` | Single `get_tracer()` pattern |
| Multi-tenant DB | `app/db.py` | `SET LOCAL` and session context |
| RLS migrations | `alembic/versions/*.py` | How RLS policies are created in migrations |
| Auth middleware | `app/middleware/auth.py` | JWT validation and Redis blocklist check |
| Auth service | `app/services/auth_service.py` | Token creation, validation, revocation |
| Test fixtures | `tests/conftest.py` | `db_session`, `client`, mock fixtures |
| Session handoff | `docs/CODEX_PROMPT.md` | Real mid-project state document |
| Review reports | `docs/audit/` | Real review cycle reports |
| CI | `.github/workflows/ci.yml` | Working CI with services |
| Architecture doc | `docs/ARCHITECTURE.md` | Format and level of detail |
| Task graph | `docs/tasks.md` | Task contract format and granularity |
