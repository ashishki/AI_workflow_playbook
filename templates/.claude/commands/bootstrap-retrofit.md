Read these local files before doing anything else:

- `PLAYBOOK.md`
- `prompts/STRATEGIST.md`
- `templates/PROJECT_BRIEF.md`
- `templates/tasks_schema.md`
- `templates/ARCHITECTURE.md`
- `templates/CODEX_PROMPT.md`
- `templates/IMPLEMENTATION_CONTRACT.md`
- `docs/usage_guide.md`

Task:

Retrofit AI Workflow Playbook onto an already existing repository without pretending it is greenfield.

Behavior:

1. Ask me for any missing current-state information needed to build the governance package:
   - what the system does today
   - current repo layout
   - current CI/test state
   - major risks and constraints
   - known backlog or remediation areas
2. Generate or update the project governance package around current repo reality:
   - `docs/ARCHITECTURE.md`
   - `docs/spec.md`
   - `docs/tasks.md`
   - `docs/CODEX_PROMPT.md`
   - `docs/IMPLEMENTATION_CONTRACT.md`
   - `docs/prompts/ORCHESTRATOR.md`
   - `docs/prompts/PROMPT_S_STRATEGY.md`
   - `docs/audit/*`
3. Build `docs/tasks.md` as a forward-looking contract for real incomplete work. Do not invent fake greenfield skeleton tasks unless the repository truly lacks that structure.
4. Use the real current baseline in `docs/CODEX_PROMPT.md`.
5. Mark only materially risky remediation/migration tasks with the optional heavy-task extension.
6. After generating the package, tell me exactly what to run next:
   - Phase 1 validation
   - Orchestrator start from the first real incomplete task
7. After listing next steps, evaluate each optional skill against the project
   signals you have collected and make a conditional recommendation:

   a. External Tools / MCP companion (`reference/external_tools_mcp_companion.md`):
      - If Tool-Use profile is ON or any MCP-shaped integration appears in the
        current repo, state: "MCP companion is active for this project — Tool
        Catalog rows must follow the schema in reference/external_tools_mcp_companion.md."
        No further confirmation needed; TOOL-6 enforces it at review.
      - Otherwise: one sentence — it exists and when to reach for it.

   b. Research Companion (EXPERIMENTAL, `reference/research_companion.md`):
      - If the current repo has a known major risk, compliance gap, or
        under-justified past decision flagged during retrofit analysis, state:
        "I recommend invoking the Research Companion for [specific question].
        Reply yes to proceed, or no to skip." Wait for the human's reply before
        invoking.
      - If no such gap is present: one sentence — it exists and when to use it.

   c. Simplification Pass (EXPERIMENTAL, `/simplify`):
      - If the repo already has substantial code: "Simplification Pass is
        available now — run `/simplify` with a file or directory scope to get
        a complexity audit."
      - Otherwise: one sentence — available after code exists.

Output requirements:

- Treat retrofit as normalization, not rewrite theatre.
- Preserve repo reality where possible.
- Escalate only the parts of governance and runtime justified by actual risk.
