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

Use the test-first route. Before changing the guard, inspect both tests and run
the declared command to establish the expected RED result. Map the failure to
the all-`uses:` allowlist criterion, then make the smallest allowed change.
Rerun the focused command to GREEN, inspect the diff, and run it once more as
the final gate. The intentional RED run is not a repair turn; after
implementation, allow at most one unexpected corrective pass. Do not weaken or
edit the staged mutation test and do not claim success from prose. End with the
RED observation, changed files, and exact final command outcome.
