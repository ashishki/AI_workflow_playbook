# Filesystem Reality Principle

## Rule

The repository is authoritative. Agent claims, chat summaries, generated
context packets, memory notes, and receipts are evidence candidates only after
they are checked against repo state.

## Authority Order

1. Filesystem and git state.
2. Tests, CI, eval artifacts, and deterministic verification output.
3. Canonical docs: architecture, contract, tasks, ADRs, review reports, evals.
4. Retrieval indexes and context packets that cite canonical artifacts.
5. Agent summaries and chat memory.

When two sources disagree, prefer the higher authority and record the mismatch
as drift.

## Operational Rules

- A task is not done because an agent says it is done.
- A file is not changed until `git diff`, file existence, or hash evidence says
  it changed.
- A test is not passed until the command output or CI result says it passed.
- A decision is not accepted until it links to an ADR, decision log entry, or
  canonical architecture update.
- A generated context packet is not trusted until its cited canonical files
  exist.

## Reviewer Check

For every implementation result, verify:

- claimed files exist or were intentionally deleted
- changed files match the declared task scope or have documented justification
- tests claimed by the implementer were actually run
- eval or evidence updates exist when capability tags require them
- `CODEX_PROMPT.md` state changes match current task and git state

If evidence is missing, return a finding. Do not ask the same implementer to
self-certify the claim.
