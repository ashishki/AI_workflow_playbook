# Problem Fit Note

Project: Receipt Audit
Mode: lean-core
Last updated: 2026-10-09

## Operational Pain

Maintainer cannot distinguish verified receipt success from missing or changed evidence by reading large JSON manually.

## Current Workaround

Manual JSON and SHA checks.

## First Proof Metric

Receipt classifier passes independent success, failure, missing, tamper and path-boundary cases.

## Out-Of-Bounds Claims Before Evidence

- production-ready autonomous system
- replaces accountable human review
- verified success without command evidence

## Verification Command

`'{python}' -m unittest discover -s tests -v`

## Current Project

T04 now provides `python3 audit_receipt.py /path/to/receipt.json` using only
the Python standard library. It returns one JSON classification after checking
stdout/stderr SHA256 evidence and the local file boundary. The supplied real
receipt returns PASS; all 13 local tests pass. Human/bootstrap acceptance (T01)
and the controller's independent read-only review remain pending.
