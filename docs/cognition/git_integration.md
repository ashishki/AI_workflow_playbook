# Git Integration Strategy

Version: 1.0
Last updated: 2026-05-25

---

## Rule

Git and markdown are the durable substrate. Obsidian, generated indexes, and vector stores are rebuildable surfaces.

---

## Sync Direction

| Direction | Allowed? | Rule |
|-----------|----------|------|
| Repo canonical docs to vault generated notes | Yes | Generated notes cite source repo/path and may be rebuilt |
| Vault manual pattern notes to repo docs | Yes, by human review | Copy or link only after the pattern changes project behavior |
| Vault generated notes to repo canonical docs | No | Fix the canonical doc directly |
| Semantic index to repo docs | No | Semantic index is discovery only |
| Context packet to implementation prompt | Yes | Packet must cite canonical artifacts |

---

## Local/VPS Operating Model

The vault does not discover work by itself. It is refreshed from Git checkouts.

Recommended layout on any machine that needs agent-readable packets:

```text
ai-stack/
|-- projects/
|   `-- <repo>/
`-- engineering-cognition-vault/
```

Local machine workflow:

1. Commit project code/docs/evals.
2. Refresh the vault without pulling project repos:

```bash
cd engineering-cognition-vault
./scripts/sync_from_projects.sh --no-pull --commit --push
```

VPS workflow:

1. Commit and push project code/docs/evals from the VPS.
2. Refresh the vault on the designated sync machine:

```bash
cd engineering-cognition-vault
git pull --ff-only
./scripts/sync_from_projects.sh --commit --push
```

If agents run on the VPS, clone the vault on the VPS and pass explicit packet
paths in prompts. Do not make project runtime depend on the vault.

Use one primary sync node where possible. Multiple machines may regenerate the
vault, but only generated outputs should be auto-committed to avoid conflicts.

For review workflows, use the freshness gate before giving packets to an agent:

```bash
cd engineering-cognition-vault
./scripts/ensure_fresh_for_project.sh <project-id> --commit --push
```

The gate compares project `HEAD` to the generated manifest's `git.head` and
refreshes the vault when the index is stale.

---

## Repo-Local Files

Recommended minimum in each project:

```text
docs/COGNITION_MANIFEST.md
generated/cognition/index.json        # optional generated output
docs/context-packets/                 # optional committed packets for major reviews only
```

Do not commit large vector indexes, Obsidian cache files, raw database exports, or local `.obsidian/workspace*` state.

---

## Generated Artifact Policy

Generated artifacts must satisfy all of the following:

- deterministic order
- source paths included
- `generated: true` when markdown
- no secrets or raw private data
- no authoritative decisions
- safe to delete and regenerate

Commit generated artifacts only when they materially improve review, auditability, or cross-session continuity. Otherwise keep them local.

---

## CI Considerations

The minimum CI check is lightweight:

- run the cognition indexer against the repo
- fail on malformed markdown frontmatter only if the repo opts into frontmatter validation
- fail if `docs/COGNITION_MANIFEST.md` links to missing canonical files
- fail if generated context packets are committed without source manifest metadata

Do not make Obsidian, vector DBs, or cloud sync part of CI.

---

## Suggested Commands

Generate a deterministic manifest:

```bash
python3 tools/cognition_index.py --root /path/to/project --output generated/cognition/index.json
```

Build a reviewer packet:

```bash
python3 tools/context_packet_builder.py \
  --manifest generated/cognition/index.json \
  --role reviewer \
  --scope "retrieval eval regression" \
  --output docs/context-packets/reviewer-retrieval-regression.md
```

Both commands operate on files only and require no Obsidian runtime.

---

## Cloud and Backup

Cloud sync is optional:

- Obsidian Sync is acceptable for vault convenience
- GitHub remote is acceptable for repo and vault backup
- Syncthing is acceptable for local-first device sync
- encrypted backups are acceptable for disaster recovery

None of these may become architectural dependencies. The system must function offline from local Git checkouts.
