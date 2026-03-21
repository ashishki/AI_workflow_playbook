# Architecture — {{PROJECT_NAME}}

Version: 1.0
Last updated: {{DATE}}
Status: Draft

---

## System Overview

{{PROJECT_NAME}} is {{ONE_PARAGRAPH_DESCRIPTION}}. It serves {{PRIMARY_USER_TYPES}} and is designed to {{PRIMARY_GOAL}}. The system {{KEY_ARCHITECTURAL_CHARACTERISTIC, e.g., "is stateless at the application layer with all persistent state in PostgreSQL and Redis"}}.

---

## Component Table

| Component | File / Directory | Responsibility |
|-----------|-----------------|----------------|
| {{COMPONENT_1}} | `{{PATH_1}}` | {{RESPONSIBILITY_1}} |
| {{COMPONENT_2}} | `{{PATH_2}}` | {{RESPONSIBILITY_2}} |
| {{COMPONENT_3}} | `{{PATH_3}}` | {{RESPONSIBILITY_3}} |
| {{COMPONENT_4}} | `{{PATH_4}}` | {{RESPONSIBILITY_4}} |

<!--
Add a row for every significant component: API layer, service layer, data access layer,
background workers, middleware, shared utilities (tracing, auth), database models/schemas.
-->

---

## Data Flow — Primary Request Path

The following steps describe the end-to-end path for a {{PRIMARY_REQUEST_TYPE, e.g., "standard authenticated API request"}}:

1. Client sends `{{HTTP_METHOD}} {{PATH}}` with {{AUTH_MECHANISM, e.g., "Bearer token in Authorization header"}}.
2. {{MIDDLEWARE_OR_GATEWAY}} validates {{WHAT_IS_VALIDATED}}.
3. {{AUTH_COMPONENT}} verifies {{AUTH_VERIFICATION_DETAIL}}.
4. Request reaches `{{HANDLER_FILE}}`. The handler extracts validated params and delegates to `{{SERVICE}}`.
5. `{{SERVICE}}` {{WHAT_SERVICE_DOES}}.
6. {{DATA_ACCESS_DETAIL, e.g., "SQLAlchemy executes a parameterized query against PostgreSQL"}}.
7. Response is constructed and returned as `{{RESPONSE_SHAPE}}`.

<!--
Write one flow for the primary use case (happy path).
Add additional flows below for background jobs, webhooks, or other significant paths.
-->

---

## Tech Stack

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Language | Python {{PYTHON_VERSION}} | {{RATIONALE}} |
| Framework | {{FRAMEWORK, e.g., FastAPI}} | {{RATIONALE}} |
| Database | {{DATABASE, e.g., PostgreSQL 16}} | {{RATIONALE}} |
| ORM / query layer | {{ORM, e.g., SQLAlchemy 2.x}} | {{RATIONALE}} |
| Cache | {{CACHE, e.g., Redis 7}} | {{RATIONALE}} |
| Task queue | {{TASK_QUEUE, e.g., "none in v1"}} | {{RATIONALE}} |
| Observability | {{TRACING, e.g., OpenTelemetry}} | {{RATIONALE}} |
| Lint / format | ruff | Unified linter and formatter; zero configuration drift |
| Test framework | pytest | Industry standard; rich fixture system |
| CI | GitHub Actions | {{RATIONALE}} |
| Deployment | {{DEPLOYMENT_TARGET}} | {{RATIONALE}} |

---

## Security Boundaries

### Authentication

{{DESCRIBE_AUTH_MECHANISM}}

Example: "All API endpoints except `/health` and `/auth/token` require a valid JWT Bearer token. Tokens are issued by `POST /auth/token` and expire after {{EXPIRY_DURATION}}. Revoked tokens are stored in Redis with TTL matching the remaining token lifetime."

### Tenant Isolation

{{IF_MULTI_TENANT: Describe how tenant isolation is enforced at each layer}}
{{IF_SINGLE_TENANT: "This is a single-tenant system. Tenant isolation is not applicable."}}

Example for RLS: "PostgreSQL Row-Level Security is enabled on all tenant-scoped tables. Every database session sets `SET LOCAL app.tenant_id = :tid` before executing any query. RLS policies enforce that `app.tenant_id` matches the `tenant_id` column on every SELECT, INSERT, UPDATE, and DELETE."

### PII Policy

No PII is stored in logs, span attributes, or metrics. The following fields are considered PII in this system: {{LIST_PII_FIELDS, e.g., "email address, full name, phone number"}}. Where these must be referenced in observability, SHA-256 hashes are used.

PII is stored in the database in the following fields: {{LIST_PII_DB_FIELDS}}. Database access to these fields is {{ACCESS_POLICY, e.g., "unrestricted within the application tier; not exposed in logs or API responses beyond what the authenticated user owns"}}.

---

## External Integrations

| Integration | Purpose | Auth method | Rate limit / SLA |
|-------------|---------|-------------|-----------------|
| {{SERVICE_1}} | {{PURPOSE_1}} | {{AUTH_1}} | {{RATE_LIMIT_1}} |
| {{SERVICE_2}} | {{PURPOSE_2}} | {{AUTH_2}} | {{RATE_LIMIT_2}} |

<!--
If there are no external integrations, write: "None in v1."
-->

---

## File Layout

```
{{PROJECT_NAME}}/
├── {{APP_DIR}}/               # Application source
│   ├── __init__.py
│   ├── {{ENTRY_POINT}}.py     # Application entry point / factory
│   ├── {{ROUTER_DIR}}/        # Route handlers (thin — delegate to services)
│   │   └── {{ROUTER_FILE}}.py
│   ├── {{SERVICE_DIR}}/       # Business logic (no HTTP dependencies)
│   │   └── {{SERVICE_FILE}}.py
│   ├── {{MODEL_DIR}}/         # Database models / schemas
│   │   └── {{MODEL_FILE}}.py
│   ├── middleware/             # Request middleware
│   │   └── auth.py
│   └── {{SHARED_UTILS}}/      # Shared utilities (tracing, config, etc.)
│       ├── tracing.py
│       └── config.py
├── tests/
│   ├── conftest.py            # Shared fixtures
│   ├── unit/                  # Unit tests (no I/O)
│   └── integration/           # Integration tests (with DB, cache)
├── {{MIGRATION_DIR}}/         # Database migrations
├── docs/
│   ├── ARCHITECTURE.md        # This file
│   ├── spec.md
│   ├── tasks.md
│   ├── CODEX_PROMPT.md
│   ├── IMPLEMENTATION_CONTRACT.md
│   ├── dev-standards.md
│   ├── audit/                 # Review cycle reports (append-only)
│   └── adr/                   # Architectural Decision Records (append-only)
├── .github/
│   └── workflows/
│       └── ci.yml
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
└── README.md
```

---

## Runtime Contract

These environment variables are required at startup. The application must fail fast with a clear error message if any required variable is absent or malformed.

| Variable | Description | Example value | Required |
|----------|-------------|---------------|----------|
| `{{ENV_VAR_1}}` | {{DESCRIPTION_1}} | `{{EXAMPLE_1}}` | Yes |
| `{{ENV_VAR_2}}` | {{DESCRIPTION_2}} | `{{EXAMPLE_2}}` | Yes |
| `{{ENV_VAR_3}}` | {{DESCRIPTION_3}} | `{{EXAMPLE_3}}` | No (default: `{{DEFAULT}}`) |

<!--
Never put credentials in this table. The "Example value" column shows the FORMAT of the value,
not a real value. Actual values live in environment variables or a secrets manager.
-->

---

## Non-Goals (v1)

The following are explicitly out of scope for v1. They may be addressed in future versions.

- {{NON_GOAL_1}}
- {{NON_GOAL_2}}
- {{NON_GOAL_3}}

<!--
Non-goals are as important as goals. They prevent scope creep and give the review agents
a clear signal when a Codex implementation is going out of scope.

Good non-goals are specific: not "we won't build X" but "we won't support Y because Z —
it will be addressed in v2 when we have ADR-004 approved."
-->
