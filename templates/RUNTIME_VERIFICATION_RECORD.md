# Runtime Verification Record

Use this artifact when a task touches risky files, command surfaces, CI,
provider/tool behavior, agent loops, correction turns, or any change where model
claims need explicit state evidence.

This record is not a verdict. It can describe intent and point to evidence, but
it must not claim that tests passed, work is verified, or a release is accepted.
Those statuses come from `tools/validate_harness_evidence.py`, independent
scorers, or a separate human-review receipt.

```yaml
type: runtime_verification_record
schema_version: playbook.runtime_verification_record.v1
task_id: T-123
intent:
  summary: "What the task intended to change."
  claimed_files:
    - path: src/example.py
      operation: modify
    - path: tests/test_example.py
      operation: create
receipt_refs:
  - receipt_id: T-123-...
    path: reports/receipts/T-123/receipt.json
post_state_manifest:
  path: reports/evidence/T-123/post_state_manifest.json
independent_scorer_outputs:
  - scorer_id: file_state
    path: reports/evidence/T-123/file_state_scorer.json
evidence_bundle:
  path: reports/evidence/T-123/bundle.json
validator_report:
  path: reports/evidence/T-123/validation_report.json
human_notes:
  - "Any residual uncertainty or manual observation goes here."
```

If a command was not run, record the missing receipt and reason:

```yaml
type: runtime_verification_record
schema_version: playbook.runtime_verification_record.v1
task_id: T-123
intent:
  summary: "Attempted risky change."
receipt_refs: []
missing_evidence:
  - kind: command_receipt
    reason: "Dependency unavailable in local environment."
next_action: blocked
human_notes:
  - "Do not treat this task as verified until a receipt and validator report exist."
```
