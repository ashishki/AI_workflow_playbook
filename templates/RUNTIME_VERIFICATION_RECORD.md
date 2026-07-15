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

For a task with UI evidence, add this optional observation block. Keep paths and
raw observations; do not add a self-issued `visual_pass` or merge verdict.

```yaml
ui_evidence:
  risk_level: medium
  visual_contract:
    declared: required
    resolved: required
  behavior_checks:
    - command: project-owned-ui-behavior-command
      result: observed_exit_and_summary
      receipt_ref: reports/receipts/T-123/ui-behavior.json
  capture_environment:
    browser: chromium
    browser_version: recorded-by-runner
    locale: en-US
    timezone: UTC
    color_scheme: light
    fonts_fixture_and_readiness: project-owned-config-ref
  viewport_coverage:
    - id: desktop-supported-breakpoint
      width: 1440
      height: 900
      device_scale_factor: 1
  stabilization:
    config_ref: project-owned-ui-test-config
    dynamic_regions:
      - target: non_acceptance_clock
        treatment: fixed_fixture
        reason: nondeterministic_value
  screenshots:
    - state: default
      viewport: desktop-supported-breakpoint
      baseline_path: reports/evidence/T-123/ui/baseline.png
      actual_path: reports/evidence/T-123/ui/actual.png
  visual_diffs:
    - state: default
      viewport: desktop-supported-breakpoint
      diff_path: reports/evidence/T-123/ui/diff.png
      observed_delta: project_tool_raw_observation
      threshold_or_rationale: predeclared_project_rule
  browser_console:
    artifact_path: reports/evidence/T-123/ui/console.txt
    policy: no_new_errors_relative_to_baseline
    observed_new_errors: 0
  baseline_updates: []
  human_review_ref: null
  vision_critic:
    used: false
    report_ref: null
  missing_evidence: []
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
