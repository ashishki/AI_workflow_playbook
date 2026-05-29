# Runtime Verification Record

Use this artifact when a task touches risky files, command surfaces, CI,
provider/tool behavior, agent loops, correction turns, or any change where model
claims need explicit state evidence.

For routine low-risk edits, a shortened record is acceptable: changed files,
`git diff --stat`, commands run, and verification status.

```yaml
type: runtime_verification
task_id: T-123
operation: file_edit
intent:
  summary: "What the task intended to change."
  claimed_files:
    - path: src/example.py
      operation: modify
    - path: tests/test_example.py
      operation: create
before_state:
  branch: main
  commit: 0123456789abcdef
  files:
    - path: src/example.py
      exists: true
      sha256: "..."
    - path: tests/test_example.py
      exists: false
      sha256: null
after_state:
  commit: fedcba9876543210
  diff_stat: |
    src/example.py          | 12 ++++++------
    tests/test_example.py   | 24 ++++++++++++++++++++++++
  files:
    - path: src/example.py
      exists: true
      sha256: "..."
      diff_verified: true
    - path: tests/test_example.py
      exists: true
      sha256: "..."
      diff_verified: true
tests_run:
  - name: targeted_unit
    command: python -m pytest tests/test_example.py -q
    status: passed
verification:
  status: passed
  failures: []
  reviewer_notes:
    - "Claimed files exist and changed as declared."
    - "No files outside task scope changed."
```

Failure example:

```yaml
type: runtime_verification
task_id: T-123
operation: file_edit
verification:
  status: failed
  failures:
    - kind: claimed_file_missing
      path: src/example.py
      detail: "Completion claimed this file was modified, but it does not exist."
    - kind: test_not_run
      command: python -m pytest tests/test_example.py -q
      detail: "Completion claimed tests passed, but no command evidence exists."
  next_action: correction_turn
  correction_attempt: 1
  max_correction_attempts: 2
```
