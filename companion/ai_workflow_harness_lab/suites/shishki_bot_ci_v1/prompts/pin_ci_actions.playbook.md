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

Use the test-first route. Before changing the workflow, inspect the staged test
and run the declared command to establish the expected RED result. Map its
failure to the immutable-reference and preserved-security acceptance criteria.
Make the smallest allowed change, rerun the focused test to GREEN, inspect the
diff, and run it once more as the final gate. The intentional RED run is not a
repair turn; after implementation, allow at most one unexpected corrective
pass. Do not weaken or edit the test and do not claim success from prose. End
with the RED observation, changed files, and exact final command outcome.
