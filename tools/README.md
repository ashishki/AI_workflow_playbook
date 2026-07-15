# Playbook Tools

These tools are deterministic helpers for cognition, integrity, and AI cost
telemetry. They do not require Obsidian, a vector database, or network access.

## Initialize a Project

```bash
python3 tools/init_playbook_project.py ../my-project \
  --mode lean-core \
  --project-name "My Project" \
  --operational-pain "Agents need a reproducible verification scaffold." \
  --current-workaround "Manual copying of playbook files." \
  --first-proof-metric "Generated project verification exits zero." \
  --verify-argv '["{python}", "-m", "pytest", "-q"]' \
  --install-claude-hooks
```

The initializer copies a proportional Lean-Core / Standard / Strict kit into a
downstream repository. It does not overwrite existing files unless `--force` is
passed. The initializer requires concrete `--operational-pain`,
`--current-workaround`, and `--first-proof-metric` values; `unknown`, `TBD`,
`TODO`, and empty values are blocked. Use `--install-claude-hooks` to safely
merge `.claude/settings.json`, copy hook scripts, set executable permissions,
and run a hook smoke test. A failed hook smoke test returns a non-zero exit.
Without that flag hooks are available but not claimed as active enforcement.
Project verification must be declared with one or more structured
`--verify-argv` JSON arrays; shell strings are not parsed into executable checks.
Use `--external-skill NAME` to create a trust-record stub before any third-party
skill is installed or enabled.

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

## Roll Up AI Cost Telemetry

```bash
python3 tools/cost_rollup.py \
  --input docs/ai_cost_telemetry.jsonl \
  --output reports/ai_cost_rollup.md \
  --strict
```

The rollup reads provider-agnostic JSONL entries matching
`schemas/cost_telemetry_entry.schema.json`, then summarizes cost by run, task,
model, and agent role. Use `--max-total-cost`, `--max-run-cost`, and
`--require-file` when `docs/COST_BUDGET.md` declares enforceable thresholds.

## Check External Skill Security

```bash
python3 tools/skill_security_gate.py \
  --root . \
  --discover-agent-skills \
  --require-scanner \
  --sarif
```

The gate discovers skills under `.codex/skills`, `.claude/skills`, and
`skills`, requires `docs/security/skills/{skill-name}/TRUST_RECORD.md`, and
runs `skillspector scan` when skills are present. Repositories with no external
skills pass without requiring SkillSpector.
