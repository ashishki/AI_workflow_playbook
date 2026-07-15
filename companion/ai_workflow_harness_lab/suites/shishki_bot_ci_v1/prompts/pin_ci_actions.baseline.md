# Pilot Task: Pin CI Actions

## Task Facts

Work only in the current isolated fixture. Do not use network access, web
search, Git remotes, parent directories, or files outside this workspace.

The CI workflow currently references mutable major-version tags. Replace them
with these approved immutable revisions:

- `actions/checkout@9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0` with comment `# v7.0.0`
- `actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1` with comment `# v6.3.0`

Preserve top-level `contents: read`, `persist-credentials: false`, and all
unrelated workflow behavior. A public acceptance test is already staged at
`pilot_tests/test_ci_pins.py`; do not modify it. The only allowed changed file
is `.github/workflows/ci.yml`.

Verification command:

```bash
python -m pytest -q pilot_tests/test_ci_pins.py
```

## Condition Workflow

Inspect the workflow and the staged acceptance test, implement the smallest
scoped correction, and run the declared verification command. If it fails,
make at most one bounded corrective pass. Do not claim success without the
command result. End with changed files and the exact verification outcome.
