Read these local files before doing anything else:

- `PLAYBOOK.md`
- `docs/project_fit_guide.md`
- `docs/adoption_modes.md`
- `docs/cost_budget_guardrails.md`
- `prompts/STRATEGIST.md`
- `templates/PROJECT_BRIEF.md`
- `templates/tasks_schema.md`
- `templates/ARCHITECTURE.md`
- `templates/CODEX_PROMPT.md`
- `templates/LEAN_CODEX_PROMPT.md`
- `templates/AGENTS.md`
- `templates/IMPLEMENTATION_CONTRACT.md`
- `templates/CONTRACT_LITE.md`
- `templates/COST_BUDGET.md`

Task:

Bootstrap a brand-new project using AI Workflow Playbook.

Behavior:

1. Ask me for any missing project-brief fields needed to complete the selected
   Phase 1 package, including `templates/PROJECT_BRIEF.md §1b Problem Fit and
   Adoption Reality`, adoption mode, and AI/model budget.
2. Choose Lean, Standard, or Strict using `docs/adoption_modes.md`. If I did
   not specify a mode, recommend one and state why. Default to Standard only
   when the evidence is ambiguous and the project is more than a tiny task.
3. Once enough information exists, generate the initial package for that mode:

   Lean:
   - `docs/tasks.md`
   - short `docs/CODEX_PROMPT.md` or `AGENTS.md`
   - `docs/CONTRACT_LITE.md`
   - documented local verification command or minimal CI
   - `docs/COST_BUDGET.md` only when AI use is recurring, multi-agent,
     dynamic-workflow based, or materially costly

   Standard/Strict:
   - `docs/ARCHITECTURE.md`
   - `docs/spec.md`
   - `docs/tasks.md`
   - `docs/CODEX_PROMPT.md`
   - `docs/IMPLEMENTATION_CONTRACT.md`
   - `docs/COST_BUDGET.md` when required by `docs/cost_budget_guardrails.md`
   - `docs/prompts/ORCHESTRATOR.md`
   - `docs/prompts/PROMPT_S_STRATEGY.md`
   - `docs/audit/*`
   - `.github/workflows/ci.yml`
   - `.claude/commands/orchestrate.md`
4. Use the task schema from `templates/tasks_schema.md`.
5. Mark only genuinely risky tasks with the optional heavy-task extension.
6. Keep the architecture minimum-sufficient. Do not over-escalate solution shape, governance level, runtime tier, capability profiles, cognition, proof receipts, or dynamic workflows without justification.
   If the brief cannot name a concrete pain, current workaround, and first proof metric, recommend a discovery / measurement phase instead of a full agentic build.
7. After generating the package, tell me exactly what to run next:
   - Phase 1 validation with the selected `Mode`
   - Lean task/review loop, or Standard/Strict Orchestrator start
8. After listing next steps, evaluate each optional skill against the project
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
