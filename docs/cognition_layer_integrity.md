# Cognition Layer Integrity

## Rule

The cognition layer is a retrieval and reasoning aid. It is never more
authoritative than the repo artifacts it cites.

## Canonical vs Generated

Canonical:

- architecture docs
- implementation contract
- task graph
- ADRs and decision logs
- evidence index
- eval artifacts
- review reports
- source code, tests, and CI

Generated or derivative:

- generated cognition indexes
- context packets
- Obsidian graph views
- summaries
- external vault mirrors

Generated artifacts are valid only while their cited canonical artifacts exist
and remain relevant.

## Integrity Checks

Before relying on a context packet:

1. Check the packet frontmatter has `canonical: false`.
2. Check every cited path exists in the repo or approved vault mirror.
3. Prefer canonical files over packet excerpts when there is conflict.
4. If the packet includes hashes, compare them with current files.
5. If citations are broken, regenerate the packet or fix the source references.

## Obsidian Interaction

Obsidian remains optional. Notes may improve navigation, but decisions,
findings, eval results, and implementation state must be written to repo
artifacts first. Vault sync is downstream of repo truth.

## Stale Memory Claim

Use this format when a cognition artifact is stale:

```yaml
type: cognition_integrity_failure
artifact: docs/context-packets/reviewer-auth.md
claim: "AUTH-ADR-003 is active"
canonical_check:
  path: docs/adr/AUTH-ADR-003.md
  status: missing
result: stale_context
next_action: regenerate_packet_or_restore_canonical_reference
```
