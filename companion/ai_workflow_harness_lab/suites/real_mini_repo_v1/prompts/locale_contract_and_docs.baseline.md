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

Inspect the test, implement the smallest-scoped correction (code + docs), and run
the command. Do not modify the fixture's tests. Do not claim success without the
command result.
