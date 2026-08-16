# Task: Round invoice tax without truncation

## Task Facts

Work only in the current isolated fixture. Do not use network access, web search,
Git remotes, parent directories, or files outside this workspace.

The billing helper currently truncates fractional cents in `billing/invoice.py`, so
an invoice subtotal that contains half-cent tax can be undercharged.

Fix `invoice_total_cents()` to keep the current contract and apply rounding to
the nearest cent using half-up behavior.

Verification command:

```bash
python -m pytest -q tests/test_invoice.py
```

## Condition Workflow

Use the test-first route.

1. Run the declared verification command before editing and capture the initial RED
   outcome.
2. Make the smallest scoped fix in `billing/invoice.py`.
3. Run the declared verification command again.
4. If necessary, inspect the diff and make at most one bounded corrective pass.

Do not modify tests. Do not claim success from prose.
