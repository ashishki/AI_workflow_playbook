Read these local files before doing anything else:

- `PLAYBOOK.md`
- `prompts/STRATEGIST.md`
- `templates/PROJECT_BRIEF.md`
- `templates/tasks_schema.md`
- `templates/ARCHITECTURE.md`
- `templates/CODEX_PROMPT.md`
- `templates/IMPLEMENTATION_CONTRACT.md`

Task:

Bootstrap a brand-new project using AI Workflow Playbook.

Behavior:

1. Ask me for any missing project-brief fields needed to complete the Phase 1 package.
2. Once enough information exists, generate the initial project governance package:
   - `docs/ARCHITECTURE.md`
   - `docs/spec.md`
   - `docs/tasks.md`
   - `docs/CODEX_PROMPT.md`
   - `docs/IMPLEMENTATION_CONTRACT.md`
   - `docs/prompts/ORCHESTRATOR.md`
   - `docs/prompts/PROMPT_S_STRATEGY.md`
   - `docs/audit/*`
   - `.github/workflows/ci.yml`
   - `.claude/commands/orchestrate.md`
3. Use the task schema from `templates/tasks_schema.md`.
4. Mark only genuinely risky tasks with the optional heavy-task extension.
5. Keep the architecture minimum-sufficient. Do not over-escalate solution shape, governance level, runtime tier, or capability profiles without justification.
6. After generating the package, tell me exactly what to run next:
   - Phase 1 validation
   - Orchestrator start
7. After listing next steps, evaluate each optional skill against the project
   signals you have collected and make a conditional recommendation:

   a. External Tools / MCP companion (`reference/external_tools_mcp_companion.md`):
      - If Tool-Use profile is ON or any MCP-shaped integration appears in the
        brief, state: "MCP companion is active for this project — Tool Catalog
        rows must follow the schema in reference/external_tools_mcp_companion.md."
        No further confirmation needed; TOOL-6 enforces it at review.
      - Otherwise: one sentence — it exists and when to reach for it.

   b. Research Companion (EXPERIMENTAL, `reference/research_companion.md`):
      - If you identify a non-trivial architecture, library, or compliance
        choice in the brief that lacks a justified ADR, state: "I recommend
        invoking the Research Companion for [specific question]. Reply yes to
        proceed, or no to skip." Wait for the human's reply before invoking.
      - If no such choice is present: one sentence — it exists and when to use it.

   c. Simplification Pass (EXPERIMENTAL, `/simplify`):
      - Always: one sentence — available after code exists, requires explicit
        `/simplify` call with user-stated scope, not relevant at bootstrap.

Output requirements:

- Write for both human review and downstream agents.
- If important information is missing, stop and ask clarifying questions instead of guessing.
- If a lower-complexity architecture is sufficient, prefer it explicitly.
