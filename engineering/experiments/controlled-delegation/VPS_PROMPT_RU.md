# Короткий промпт для VPS-агента

```text
Работаем в `ashishki/AI_workflow_playbook` на ветке
`feature/controlled-delegation-20261008`. Master не меняй и не мержи.

1. Проверь HEAD, чистоту worktree и прочитай AGENTS.md плюс
   `engineering/experiments/controlled-delegation/README.md`.
2. Сначала прогони source tests:
   - `python -m unittest discover -s tests/vnext -p "test_*.py" -v`
   - `python tools/vnext_check.py --root .`
   - затронутые Native/Desktop tests и `git diff --check`.
3. Подготовь эксперимент командой `evaluate.py prepare`, указав точную модель и HEAD.
4. Выполни все A/B/C workspaces в порядке `run-plan.json`, каждый в новой сессии.
   Не меняй модель, reasoning, permissions или исходные task files между условиями.
   Raw logs оставляй в `.playbook-artifacts/`; secrets и частные данные не используй.
5. Для C соблюдай: один orchestrator, self/delegate/ask/stop, max 3 parallel,
   depth 1, один writer на mutable area, не более 3 meaningful checkpoints.
6. Заполни каждый `run-result.json` только наблюдаемыми данными. Если native subagents,
   usage/cost или fresh-session evidence недоступны — ставь BLOCKED/NOT_RUN, не PASS.
7. Выполни `collect` и `report` в `reports/delegation/2026-10-08/`.
8. Проведи один независимый read-only review итогового diff/отчёта; исправь только
   подтверждённые проблемы и повтори релевантные проверки.
9. Commit: `feat(experiment): add controlled delegation evaluation results`.
   Push только в текущую ветку.

В финале сообщи commit SHA, PASS/FAIL/NOT RUN, решение отчёта, пути к evidence,
ссылку/номер CI и что всё ещё не доказано. Не исправляй исторические frozen pilot
artifacts ради зелёного статуса и не мержи в master.
```
