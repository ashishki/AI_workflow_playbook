# Pilot Task: Reject Unapproved CI Actions

## Task Facts

Work only in the current isolated fixture. Do not use network access, web
search, Git remotes, parent directories, or files outside this workspace.

The current supply-chain regression checks only `uses:` entries under the
`actions/*` namespace. Harden `tests/test_ci_supply_chain.py` so every `uses:`
reference is parsed and accepted only when both its action name and immutable
revision match `PINNED_OFFICIAL_ACTIONS`. A mixed third-party reference must be
rejected while the approved workflow continues to pass.

A public mutation regression is staged at
`pilot_tests/test_unapproved_action.py`; do not modify it. The only allowed
changed file is `tests/test_ci_supply_chain.py`.

Verification command:

```bash
python -m pytest -q tests/test_ci_supply_chain.py pilot_tests/test_unapproved_action.py
```

## Condition Workflow

Inspect the existing guard and staged regression, implement the smallest
scoped correction, and run the declared verification command. If it fails,
make at most one bounded corrective pass. Do not claim success without the
command result. End with changed files and the exact verification outcome.
