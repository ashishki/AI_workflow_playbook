# Obsidian Vault Template

This directory documents the recommended vault structure for the playbook cognition layer. Copy this structure into a separate vault repository or sibling directory when you want Obsidian as a human graph UI.

```text
engineering-cognition-vault/
|-- 00-operating-model/
|-- 10-projects/
|-- 20-decisions/
|-- 30-evals/
|-- 40-findings/
|-- 50-patterns/
|-- 60-research/
|-- 70-postmortems/
|-- 80-agent-profiles/
|-- 90-context-packets/
|-- _generated/
`-- _templates/
```

Rules:

- project repositories remain authoritative
- generated notes may be deleted and rebuilt
- manual notes must cite canonical repo artifacts
- Obsidian plugins and cloud sync are optional
- retrieval scripts must work without Obsidian running

See `docs/cognition/obsidian_vault_architecture.md` for the full contract.
