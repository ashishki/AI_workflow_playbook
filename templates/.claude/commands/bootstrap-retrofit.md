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
7. After listing next steps, briefly surface the optional skills available in
   `reference/optional_skills.md`. For each registered skill, state in one
   sentence when it is useful and whether it is opt-in or EXPERIMENTAL. Do not
   activate any skill automatically — the human decides.

Output requirements:

- Treat retrofit as normalization, not rewrite theatre.
- Preserve repo reality where possible.
- Escalate only the parts of governance and runtime justified by actual risk.
