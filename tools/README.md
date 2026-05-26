# Cognition Tools

These tools are deterministic helpers for the markdown cognition layer. They do not require Obsidian, a vector database, or network access.

## Build a Manifest

```bash
python3 tools/cognition_index.py --root . --output generated/cognition/index.json
```

The manifest scans canonical markdown-oriented project surfaces, classifies artifact kinds, extracts headings and links, and records content hashes.

## Build a Context Packet

```bash
python3 tools/context_packet_builder.py \
  --manifest generated/cognition/index.json \
  --role reviewer \
  --scope "retrieval eval regression" \
  --output docs/context-packets/reviewer-retrieval-regression.md
```

Packets are generated markdown. They cite canonical source files and should stay bounded to the role and scope.

## Check Reference Integrity

```bash
python3 tools/integrity_check.py --root .
```

The checker is read-only. It verifies common playbook references such as
`Context-Refs`, `docs/EVIDENCE_INDEX.md` artifact paths, cognition manifest
paths, and generated context packet citations. Use `--strict-generated` when a
project intentionally commits generated packets and wants missing packet
references to fail CI.
