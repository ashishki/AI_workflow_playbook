# Handoff: Codex frontend skills and optional MCP

Status: **PROPOSED / documentation-only**. Date: 2026-09-19.
Repository: `ashishki/AI_workflow_playbook`.
Research baseline: `d570163ab17ec3b4245187c778f1e8d89af9690f` (`master`).
Publication branch: `docs/codex-frontend-skills-mcp-20260919`.

## Request and delivered scope

The user requested deeper research into skills used by mysetup.ai authors, especially frontend; whether an equivalent workflow can use Codex without Claude; when MCP is useful; a detailed proposal, ordered implementation and quality evaluation with explicit responsibilities; and publication on a separate branch.

This branch contains only research, a proposed plan, this handoff, and documentation navigation. It does not install skills/MCP, change production code, implement CF stages, approve a Feature Design, or authorize merge/deployment. Publishing the proposal is not approval to execute it.

Read:

- [Research and proposal (Russian)](../research/CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md)
- [Implementation and evaluation plan (Russian)](../research/CODEX_FRONTEND_IMPLEMENTATION_PLAN_RU.md)
- [Documentation index](../README.md)

## Findings to preserve

Codex-only is a proposed complete development process, not a promise that all models produce identical frontend quality. Skills provide scoped instructions; tools provide capabilities; MCP is an optional interface to tools and external context, not a required dependency of the user's products.

At the research baseline, `tools/skill_security_gate.py` discovers `.codex/skills`, `.claude/skills`, and `skills`, but not native `.agents/skills`. The proposal prioritizes effective discovery and trust coverage before installing a frontend pack. `tools/render_slice_context.py` uses character clipping and skips some absent manifest paths; required-context coverage needs explicit validation. Existing execution receipts do not require observed application build identity; browser evidence should prove the correct implementation was exercised.

Reuse Codex Direct, the existing four-role reviewer harness, `docs/testing/ui_verification.md`, `feature_workflow` and Harness Lab. Do not add a parallel orchestrator, scheduler, approval system, universal memory service, or mandatory React/browser/MCP dependency.

## Verification performed and limitations

Research used GitHub connector reads and public primary documentation. The main research file records sources and versions where available. Community claims are self-reports; private skills were not audited as source code. No source was installed or executed merely because it appeared on mysetup.

An isolated reproduction of the discovery traversal was executed on temporary fixtures. With a skill only in `.agents/skills`, discovered targets were `[]`. Adding `.codex/skills/legacy-check` discovered only that legacy path. This was a copy of the traversal logic, not execution of the full repository security CLI, external scanner or installed Codex.

Local `git clone` failed with DNS resolution for github.com. A public archive retrieval was also unavailable. There was no accessible `codex` executable. Accordingly:

| Check | Status in this authoring session |
|---|---|
| Read named repository files at pinned baseline | Performed via GitHub connector |
| Isolated discovery algorithm reproduction | Performed; narrow result above |
| Full repository `pytest` | NOT_RUN |
| `tools/verify_playbook.py` / full integrity checker | NOT_RUN |
| Live Codex skill compatibility smoke | NOT_RUN |
| Independent Role Runner review | NOT_RUN |
| Frontend quality or MCP A/B pilot | NOT_RUN |

Documentation-only static checks and remote publication verification are separate from these runtime checks. Consult the publication response/commit for actual results; do not infer green CI from the existence of a branch. The existing CI configuration targets pushes to master/main and pull requests, so a side-branch push alone does not establish a CI result.

## Next-session operating instructions

First inspect the actual workspace, branch, HEAD, dirty state and changes relative to the current remote base. Preserve unrelated work. Fetch only when network access is permitted. Start from this branch for proposal revisions; create a separate implementation branch only after the approved design/task scope says to do so. Never edit master directly.

Read the two linked documents, then current `PLAYBOOK.md`, `docs/CODEX_PROMPT.md`, `docs/tasks.md`, `docs/adoption_modes.md`, `docs/codex_role_execution_harness.md`, and relevant canonical security/UI policies. Use their current authority, not this historical handoff, to resolve disagreements. Do not restart completed historical task queues.

Begin with CF-00: inventory, real downstream task selection, observed baseline, Feature Design and required reviews. CF identifiers are proposal labels, not existing task IDs. Map them to real task/feature/slice records. The user has not selected a downstream frontend repository in this request; do not assume a React stack or silently modify another repository.

Present scope, evidence contract, cost/permission budgets and unresolved product decisions for human approval. Do not self-approve, synthesize a human identity, bypass interactive approval, or install all suggested packages while waiting for design acceptance.

After approval, implement in bounded slices with tests first where required. Use the actual configured model/effort; no silent reviewer downgrade. Invoke only the four supported roles through the existing Role Runner. An implementer's self-check is not independent review. A QA driver that launches a browser and changes test data is not read-only.

The baseline frontend pilot uses no MCP. CF-07 is conditional and may be explicitly skipped as not useful. Compare current competent workflow against skills, then compare browser interfaces separately. Preserve holdouts, failures, manual hints and cost uncertainty. Do not fill an experiment report with invented outcomes.

For each completed slice record exact changed files/commits, actual commands/results, receipts, evidence freshness, independent reviews, human gates, remaining findings, rollback and the next action. Merge/release remains human.

## Copyable starting prompt

```text
Продолжи в ashishki/AI_workflow_playbook, ветка
 docs/codex-frontend-skills-mcp-20260919.

Сначала покажи git status, ветку, HEAD и изменения относительно актуальной
базы. Не трогай master и не перезапускай закрытые исторические задачи.
Прочитай docs/handoffs/CODEX_FRONTEND_SKILLS_MCP_HANDOFF.md и два документа,
на которые он ссылается; затем сверь текущие canonical policy и task state.

Цель — подготовить и после требуемого approval реализовать proposed план
CF-00–CF-09: Codex-only frontend workflow, scoped skills, проверяемое browser
evidence и MCP только при доказанной необходимости. Не подменяй цель
массовой установкой plugins или новым универсальным runtime.

Сейчас начни с CF-00: inventory, baseline, Feature Design, существующие
required design reviews и предъявление владельцу. Документы этой ветки
не означают утверждения дизайна или разрешения менять downstream repo.
После approval двигайся по зависимостям небольшими проверяемыми слайсами.
Сохраняй текущую модель/effort и review policy; не выдумывай результаты
проверок и не объявляй собственное ревью независимым.
```
