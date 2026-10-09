# Playbook — текущая работа и фактические границы

Обновлено 9 октября 2026. Технические результаты и отчёт о живых моделях вошли
в master через [PR #13](https://github.com/ashishki/AI_workflow_playbook/pull/13),
merge `d003bf76cff384d965d6c72f68934b382ae54c0f`; все три CI этого коммита PASS.
[Общий CI](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37928767543),
[Native](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37928767839),
[vNext](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37928767662).
Это проверенная база следующего шага. Актуальный HEAD получить перед новой работой.
Downstream и production не обновляются этим кодом.

vNext уже слит через PR #9. Результаты Controlled Delegation вошли через
[PR #11](https://github.com/ashishki/AI_workflow_playbook/pull/11).
Предыдущая записка сохранена [побайтно](history/STATUS.before-delivery-acceptance-20261009.md).
Текущая очередь — [D00–D10](../delivery/PLAN_RU.md),
[приёмка на VPS](../delivery/VPS_ACCEPTANCE_RU.md).

## Что исправляется и для чего

- D00: dev install Harness Lab, полный pytest, source archive вместо сравнения
  старого manifest с современным деревом, явные NOT RUN для исторического host,
  достоверные ссылки на отсутствующие старые свидетельства. История не переписана.
- Source Delivery из PR #10 объединён с актуальным master; Discover outcome и
  Verify decision-boundary улучшения сохранены. D00 commit `d2105d0`, source merge
  `2225a3f`. Перенос source не является автоматической приёмкой D01–D10.
- Native/Desktop `0.2.0-preview.4`: проверка helper pointer, interrupted journal,
  отказ при missing/foreign transaction, рабочая managed review command.
  Private evaluation preview; права распространения и выпуск отдельно.

Техническая приёмка source `7f36b90`: full pytest 320 PASS / 2 historical NOT RUN,
canonical PASS, vNext 50 PASS, Desktop 20 PASS, Native package 24 PASS без root.
Все три exact-source CI workflows PASS: Windows/macOS/Linux сборки и браузер,
Python 3.10/3.13, Engineering regressions и общий verifier.

Linux frozen ZIP проверен через реальные CLI/GUI install/update/remove/rollback;
Native payload совпал с независимой сборкой. Новый синтетический APP прошёл
HTTP/browser/recovery/export/off-state. Отдельный агент без прежнего чата изменил
правило, сохранил старые данные и прошёл внешние проверки.
[Итог и все границы](../../reports/delivery/2026-10-09/REPORT_RU.md),
[машинные результаты](../../reports/delivery/2026-10-09/results.json),
[D00 история отрицательных исходов](../../reports/delivery/2026-10-09/D00_REPORT_RU.md).

Настоящие модели теперь проверены: OpenCode 1.18.34 с существующим Go доступом,
Codex exec 0.162.0 через существующий аккаунт; модельные процессы UID998.
ENG-NEW: 13 тестов проекта / 12 внешних групп; ENG-CHANGE: 17 / 16, чужие данные
сохранены. Для обеих версий actual Native slice_review validated/PASS и отдельный
verify valid/PASS. AI-EVAL 6/6 PASS на безопасном синтетическом корпусе; NO-CODE
оставил существующую таблицу. Отказы 403/429, timeouts и ошибочный первый transport
сохранены. Ключи остались в исходном профиле, временные relays остановлены.
[Живые модели: отчёт](../../reports/delivery/2026-10-09-live-models/REPORT_RU.md),
[результаты и ограничения](../../reports/delivery/2026-10-09-live-models/results.json).

Первый незавершённый полный шаг — D02: технические маршруты пройдены с явно
учтённой помощью координатора; полная самостоятельность не доказана. D03/D06–D10
не получают full PASS из source merge или синтетических сценариев. Независимые
source reviewers нашли и исправили P2; отчёт reviewer хранится с reviewed identities.

## Что остаётся открытым

Полные реальные пользовательские истории, field-пилот, live AI/data integration,
Preview → Claim с owner account/Terms, чистые машины Windows/macOS/Linux и release
approval пока не подтверждены. Техническая автоматизация, fake CLI и синтетический
пример не закрывают эти пункты. Отсутствие model access больше не является
наблюдаемым blocker: рабочий путь non-root CLI подтверждён. При следующих calls
сохранить разрешённый provider/model/budget и проверять текущие лимиты; старое
root exception относилось к шести R3 и не переносится на Delivery.

Следующий согласованный шаг — одна настоящая рабочая задача с участником.
Сейчас статус **NOT RUN**: конкретная проблема, участник и разрешённые примеры
ещё не зафиксированы. Нужно описать нынешний способ работы, выбрать достаточное
решение, использовать его и позднее попросить изменение в новой сессии.
Записать эффект, ошибки, сохранность данных, затраты и всю помощь автора.
[Порядок действий](../delivery/PLAN_RU.md#следующий-рабочий-шаг-одна-настоящая-задача),
[начало пилота](../../product/pilots/README.md#с-чего-начать-сейчас).
Проверки интеграций, публичного владения и установки на чистые машины остаются
в очереди; они выполняются до соответствующего внедрения или выпуска.

## Вывод эксперимента по делегированию

[Архив](../../reports/delegation/README.md) сохранён. В R3 при одинаковом качестве
всех шести результатов C медленнее B в 1.46 раза; uncached input выше в 2.93 раза,
output — в 1.69 раза. Добавочная польза на этих сценариях не показана. Один
implementation-агент остаётся исходным вариантом; независимый review сохраняется.
USD и время человека неизвестны, qualification BLOCKED. Новая Delivery-проверка
не превращает эти результаты в доказанную production-пользу.

В новом instruction-only plain/Playbook сравнении результат также 1/2 у обоих,
Playbook медленнее (37.94s против 24.93s средних main sessions). Независимый review
нашёл ложные claims об отсутствии файловых изменений. Это конкретная польза
проверки результата; дополнительное делегирование автоматически не включено.
Go CLI estimate для наблюдаемой части нового опыта $0.045424519; полной суммы нет.
