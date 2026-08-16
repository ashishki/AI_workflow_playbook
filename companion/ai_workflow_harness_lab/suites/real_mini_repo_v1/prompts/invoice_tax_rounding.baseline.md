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

Inspect the test, implement the smallest-scoped correction, and run the command.
Do not modify the fixture's tests. Do not claim success without command output.
