# Task: Normalize locale inputs and document accepted values

## Task Facts

Work only in the current isolated fixture. Do not use network access, web search,
Git remotes, parent directories, or files outside this workspace.

Locale normalization in `locales/normalizer.py` accepts tag variants but returns
them unchanged; callers depend on canonical `en`/`ru` values.

Fix `normalize_locale()` to:

- lower-case safely,
- collapse region tags (`en-US` -> `en`, `ru-RU` -> `ru`),
- reject unsupported locales with `ValueError`.

Update `README.md` with a concrete supported-locale contract.

Verification command:

```bash
python -m pytest -q tests/test_locale_normalizer.py
```

## Condition Workflow

Use the test-first route.

1. Run the declared verification command before editing and capture the initial RED
   outcome.
2. Make the smallest scoped fix in `locales/normalizer.py` and `README.md`.
3. Run the command again as the final gate.
4. If needed, inspect the diff and make at most one bounded corrective pass.

Do not claim success from prose.
