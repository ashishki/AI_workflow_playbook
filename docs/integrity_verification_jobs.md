# Integrity Verification Jobs

## Purpose

Catch broken references, stale generated context, missing evidence, and
unverified claims before they become review or phase-gate drift.

## Read-Only Checks

Run these locally or in CI:

- task `Context-Refs` point to existing files
- `docs/EVIDENCE_INDEX.md` artifact paths exist
- `docs/COGNITION_MANIFEST.md` canonical and generated paths exist when they are
  committed policy
- generated context packets cite existing canonical files
- eval artifacts referenced by active profiles exist
- open findings point to existing review reports or source files
- runtime verification records, when present, have claimed files and tests

## Suggested CI Job

```yaml
name: Integrity

on:
  pull_request:
  push:
    branches: [main]

jobs:
  integrity:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: python tools/integrity_check.py --root .
```

## Failure Policy

- Missing canonical artifact: fail CI.
- Missing generated packet: warn unless the project explicitly commits packets.
- Broken evidence path for active profile: fail CI.
- Broken optional reference in inactive profile: warn.
- Stale hash: fail only when the record declares hash verification required.

## Metrics

Track:

- broken Context-Refs rate
- stale generated packet rate
- missing evidence rows
- unresolved findings without evidence
- time-to-detect stale cognition artifacts
