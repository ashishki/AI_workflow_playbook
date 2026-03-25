# Domain Skeleton: Healthcare / HIPAA

<!--
Use this skeleton when:
- Compliance Profile = ON
- Active framework includes HIPAA (or HITECH)
- System handles PHI fields

How to use:
1. The Strategist includes these pre-built tasks in docs/tasks.md when the above conditions apply.
2. Replace {{...}} placeholders with project-specific values.
3. Merge with the standard T01/T02/T03 skeleton — these tasks typically begin at T04 or later.
4. Add project-specific tasks (e.g., appointment CRUD, HL7/FHIR integration) after these.

These tasks are ordered by dependency. Do not reorder without reviewing Depends-On chains.
-->

---

## T-HC-01: PHI Field Classification and Enforcement

Owner:      codex
Phase:      1
Type:       compliance:control
Depends-On: T01

Objective: |
  Implement field-level PHI classification enforcement. Identify all PHI fields defined
  in ARCHITECTURE.md §Data Classification and ensure none appear in log messages, span
  attributes, metrics labels, or API error responses. Implement a PII-scrubbing log
  formatter and a span attribute allowlist at the shared tracing module boundary.

Acceptance-Criteria:
  - id: AC-1
    description: "A request handler that processes PHI fields produces log output containing only SHA-256 hashed identifiers — no raw PHI values. Verified by asserting log records contain no literal PHI field values."
    test: "tests/compliance/test_phi_enforcement.py::test_phi_not_in_logs"
  - id: AC-2
    description: "OpenTelemetry spans produced during PHI-touching operations contain no PHI field names or values in span attributes. Verified by inspecting exported spans."
    test: "tests/compliance/test_phi_enforcement.py::test_phi_not_in_spans"
  - id: AC-3
    description: "API error responses for endpoints that handle PHI contain no PHI values — only opaque identifiers or generic messages."
    test: "tests/compliance/test_phi_enforcement.py::test_phi_not_in_error_responses"
  - id: AC-4
    description: "docs/compliance_eval.md PHI enforcement control row has status=Implemented, evidence=tests/compliance/test_phi_enforcement.py, last verified date=today."
    test: "tests/compliance/test_compliance_eval.py::test_phi_control_evidence_current"

Files:
  - app/logging/phi_scrubber.py        # created — log formatter that scrubs PHI fields
  - app/tracing/span_allowlist.py      # created — span attribute allowlist enforced at tracing boundary
  - app/config/phi_fields.py           # created — single source of truth for PHI field names
  - tests/compliance/test_phi_enforcement.py   # created
  - tests/compliance/test_compliance_eval.py   # created
  - docs/compliance_eval.md            # updated

Notes: |
  PHI field list is sourced from ARCHITECTURE.md §Data Classification. Do not hardcode
  field names in the scrubber — load from app/config/phi_fields.py. The log formatter
  wraps the standard logging.Formatter; integration point is the root logger configuration
  in app/main.py. Tracing integration point is app/tracing/__init__.py::get_tracer().

---

## T-HC-02: Audit Log Infrastructure

Owner:      codex
Phase:      1
Type:       compliance:audit
Depends-On: T01, T-HC-01

Objective: |
  Implement the HIPAA-compliant audit log: an append-only PostgreSQL table that records
  every security-relevant event (authentication, authorization, PHI access, PHI mutation,
  PHI deletion, admin actions). The table must be tamper-evident — DELETE privilege revoked
  at the database level. Audit writes are transactional with the events they record.

Acceptance-Criteria:
  - id: AC-1
    description: "Migration creates audit_log table with columns: id (uuid), timestamp (timestamptz not null), actor_id (text not null), action (text not null), resource_type (text not null), resource_id (text), result (text not null), trace_id (text). No nullable constraint violations on required fields."
    test: "tests/compliance/test_audit_log.py::test_audit_table_schema"
  - id: AC-2
    description: "Attempting DELETE on the audit_log table raises PermissionDenied or equivalent database error. Verified against a test database where the application role lacks DELETE privilege."
    test: "tests/compliance/test_audit_log.py::test_audit_log_delete_rejected"
  - id: AC-3
    description: "AuditService.record() writes exactly one row per call containing all required fields. Verified by reading back the inserted row."
    test: "tests/compliance/test_audit_log.py::test_audit_record_written"
  - id: AC-4
    description: "A failed application transaction (simulated DB error) does not produce an audit log entry for the failed action — no phantom audit rows from rolled-back transactions."
    test: "tests/compliance/test_audit_log.py::test_no_phantom_audit_on_rollback"
  - id: AC-5
    description: "docs/compliance_eval.md audit log control row has status=Implemented, evidence=tests/compliance/test_audit_log.py, last verified date=today."
    test: "tests/compliance/test_compliance_eval.py::test_audit_control_evidence_current"

Files:
  - migrations/{{VERSION}}_create_audit_log.py   # created — migration with DELETE privilege revoke
  - app/services/audit.py                         # created — AuditService with record() method
  - tests/compliance/test_audit_log.py            # created
  - tests/compliance/test_compliance_eval.py      # modified
  - docs/compliance_eval.md                       # updated

Notes: |
  The DELETE REVOKE must appear in the migration, not only in application code. Use:
  `REVOKE DELETE ON audit_log FROM {{APP_DB_ROLE}};` after table creation.
  AuditService.record() must be called inside the same database transaction as the
  application event it records. Do not use a separate background task or async queue
  for audit writes — a queue failure would create an audit gap, which is a HIPAA violation.

---

## T-HC-03: Data Retention Policy Enforcement

Owner:      codex
Phase:      2  # move to Phase 3+ if the core data model extends beyond Phase 1
Type:       compliance:control
Depends-On: T-HC-01, T-HC-02

Objective: |
  Implement the HIPAA data retention policy: PHI records older than the retention
  threshold defined in ARCHITECTURE.md §Audit Log Requirements are either archived
  to a WORM-compliant store or securely deleted. The policy is enforced by a scheduled
  job (not manual process) and is fully testable via the retention boundary.

Acceptance-Criteria:
  - id: AC-1
    description: "RetentionService.run() archives or deletes PHI records with created_at older than RETENTION_DAYS. Returns count of records processed. Verified with a fixture containing one record inside and one outside the retention window."
    test: "tests/compliance/test_retention.py::test_retention_boundary"
  - id: AC-2
    description: "RetentionService.run() produces an audit log entry for each record it archives or deletes, with action='retention_archive' or 'retention_delete'. No PHI values in the audit entry."
    test: "tests/compliance/test_retention.py::test_retention_audit_logged"
  - id: AC-3
    description: "The scheduled retention job is registered and visible in the job scheduler (Celery beat schedule or equivalent). A test verifies the job registration exists with the correct interval."
    test: "tests/compliance/test_retention.py::test_retention_job_registered"
  - id: AC-4
    description: "RETENTION_DAYS is loaded from environment variable, not hardcoded. Default value matches ARCHITECTURE.md §Audit Log Requirements. Verified by overriding the env var in a test."
    test: "tests/compliance/test_retention.py::test_retention_days_configurable"
  - id: AC-5
    description: "docs/compliance_eval.md retention policy control row has status=Implemented, evidence=tests/compliance/test_retention.py, last verified date=today."
    test: "tests/compliance/test_compliance_eval.py::test_retention_control_evidence_current"

Files:
  - app/services/retention.py                    # created — RetentionService
  - app/tasks/retention_job.py                   # created — scheduled job wrapper
  - tests/compliance/test_retention.py           # created
  - tests/compliance/test_compliance_eval.py     # modified
  - docs/compliance_eval.md                      # updated

Notes: |
  RETENTION_DAYS default for HIPAA is 2190 (6 years). Confirm with ARCHITECTURE.md
  §Audit Log Requirements. For audit_log records: HIPAA requires 6-year retention,
  so RetentionService must NOT delete audit_log rows within the retention window —
  only application data records. Audit log rows follow a separate, longer retention
  schedule. Clarify scope at task start by re-reading ARCHITECTURE.md §Data Classification.

---

## T-HC-04: Compliance Evidence Collection

Owner:      codex
Phase:      3  # run in the final phase before launch; adjust to match your total phase count
Type:       compliance:evidence
Depends-On: T-HC-01, T-HC-02, T-HC-03

Objective: |
  Complete the HIPAA compliance evidence artifact (docs/compliance_eval.md): verify
  every control row is marked Implemented with a valid evidence file path and a
  current last-verified date. Produce a final evidence summary for the BAA and
  attestation process.

Acceptance-Criteria:
  - id: AC-1
    description: "Every row in docs/compliance_eval.md has status=Implemented (no Partial or Not Started rows). Verified programmatically by parsing the table."
    test: "tests/compliance/test_compliance_eval.py::test_all_controls_implemented"
  - id: AC-2
    description: "Every evidence file path in docs/compliance_eval.md points to a file that exists in the repository."
    test: "tests/compliance/test_compliance_eval.py::test_evidence_files_exist"
  - id: AC-3
    description: "Every last-verified date in docs/compliance_eval.md is within the last 30 days (not stale)."
    test: "tests/compliance/test_compliance_eval.py::test_evidence_dates_current"

Files:
  - docs/compliance_eval.md                      # finalized
  - tests/compliance/test_compliance_eval.py     # finalized

Notes: |
  This task does not write application code. It is a verification and documentation task.
  If any control is Partial or Not Started when this task begins, create a FIX-NN entry
  in docs/CODEX_PROMPT.md Fix Queue before starting — do not mark T-HC-04 DONE until
  all controls are Implemented.

---

## Capability Profile Table Entry (ARCHITECTURE.md)

When these tasks are included, add to the Capability Profiles table:

```markdown
| Compliance | ON | `docs/compliance_eval.md` | The system processes PHI under HIPAA. A BAA is required before launch and audit logs must be retained for 6 years (HIPAA minimum). Compliance evidence collection is a launch gate, not a post-launch task. |
```

## IMPLEMENTATION_CONTRACT.md Addition

Include `## Profile Rules: Compliance` from `templates/IMPLEMENTATION_CONTRACT.md` verbatim. Set `RETENTION_DAYS = 2190` (6 years) in the Max Index Age equivalent field.

## compliance_eval.md Starter

Create `docs/compliance_eval.md` with this initial control table:

| Control ID | Framework | Description | Status | Evidence | Last verified |
|------------|-----------|-------------|--------|----------|---------------|
| HIPAA-PHI-01 | HIPAA Privacy Rule | PHI field classification and enforcement (no PHI in logs/spans) | Not Started | — | — |
| HIPAA-AUDIT-01 | HIPAA Security Rule §164.312(b) | Audit log: append-only, tamper-evident, all required events covered | Not Started | — | — |
| HIPAA-RETAIN-01 | HIPAA §164.530(j) | PHI records retained for minimum 6 years; policy enforced in code | Not Started | — | — |
| HIPAA-ACCESS-01 | HIPAA Security Rule §164.312(a) | Access controls: authentication required before PHI access | Not Started | — | — |
| HIPAA-TRANS-01 | HIPAA Security Rule §164.312(e) | PHI in transit protected by TLS 1.2+ only | Not Started | — | — |
