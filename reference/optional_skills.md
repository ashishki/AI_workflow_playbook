# Optional Skills

Optional, opt-in capabilities layered on top of the AI Workflow Playbook. Each
skill is described using the format in `templates/skills/SKILL_INTERFACE.md`.

Skills extend the workflow without modifying canonical artifacts (`PLAYBOOK.md`,
`IMPLEMENTATION_CONTRACT.md`, `ARCHITECTURE.md`, `spec.md`, `tasks.md`,
`CODEX_PROMPT.md`). They produce retrieval surfaces, finding reports, or
proposed task drafts. They never apply changes directly.

The center of gravity remains the Strategist → Phase 1 Validator → Orchestrator
→ Codex → review loop. A skill is rejected if it competes with those roles or
relaxes any contract rule.

---

## Registered Skills

| Skill | Status | Allowed Role | Output | Descriptor |
|-------|--------|--------------|--------|------------|
| External Tools / MCP | optional | Strategist, Reviewer, Human | Proposed Tool Catalog rows; audit-log shape; env-var entries; tool-task drafts | [`templates/skills/external_tools_skill.md`](../templates/skills/external_tools_skill.md) — guide: [`reference/external_tools_mcp_companion.md`](external_tools_mcp_companion.md) |

---

## How to Add a Skill

1. Copy `templates/skills/SKILL_INTERFACE.md` to a new descriptor file.
2. Fill in every required field. A descriptor with a missing field is rejected.
3. Add a row to the Registered Skills table above.
4. If the skill is `experimental`, add a `Status: EXPERIMENTAL` line at the top
   of the descriptor and link any evaluation results in `docs/research/` once
   they exist.
5. Skills do not require an ADR to add or remove. They are documentation
   surfaces, not contract changes.

---

## Out of Scope for Skills

Skills are not the right shape for any of the following — use the playbook's
existing mechanisms instead:

| Need | Use |
|------|-----|
| New review check | extend `prompts/audit/PROMPT_2_CODE.md` with a SEC / QUAL / profile-tagged check |
| New runtime mode | declare in `docs/ARCHITECTURE.md` Runtime tier and update `docs/IMPLEMENTATION_CONTRACT.md §Control Surface` |
| New capability behavior (RAG / Tool-Use / Agentic / Planning / Compliance) | activate the corresponding profile in Phase 1 |
| Hard rule for every project | propose an addition to `IMPLEMENTATION_CONTRACT.md §Universal Rules` via ADR |
| Multi-step orchestration | extend `prompts/ORCHESTRATOR.md`, not a skill |
