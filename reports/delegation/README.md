# Controlled Delegation reports

Архив трёх фактически выполненных раундов:

- [Первый раунд](2026-10-08/REPORT_RU.md).
- [Второй раунд](2026-10-08-round2/REPORT_RU.md).
- [Третий раунд](2026-10-08-round3/REPORT_RU.md): все шесть приложений 100/100;
  делегирование медленнее одного Playbook-агента в 1.46 раза, uncached input выше
  в 2.93 раза. Польза на этом сценарии не показана; qualification BLOCKED.

Подготовленный перенос в master содержит этот архив и поясняющую документацию.
Runtime Playbook, Delivery/Desktop и
автоматическое включение делегирования этим переносом не меняются. Исполняемый
harness сохранён в [исходной версии экспериментальной ветки](https://github.com/ashishki/AI_workflow_playbook/tree/ad55ee487ea0ff3b62ac9aefdfbdef115dcb7516/engineering/experiments/controlled-delegation).
Замороженные preflight, исходные FAIL/STOP_SHIP и последующие исправления сохранены.

При переносе восстановлены два архивных экземпляра одного Python bytecode cache,
ранее проигнорированного Git. Его точные локальные байты совпали с SHA256,
указанным в исходных индексах; индексы и отчёты не переписывались. Все 676
индексированных ссылок архива прошли побайтную проверку. Кеш хранится лишь как
историческое свидетельство внутри reports и не входит в рабочий runtime.

Отчёты здесь создаются только после фактических A/B/C-прогонов из
`engineering/experiments/controlled-delegation/`.

До запуска не добавляйте заполненный `REPORT_RU.md` или PASS-статусы. Генератор
сохраняет нормализованный `results.json`, механические проверки и рекомендацию:
`ENABLE_CONDITIONALLY`, `KEEP_EXPERIMENTAL` или `REVISE_OR_REJECT`.

Raw agent chats/traces остаются в `.playbook-artifacts/` и не коммитятся. В Git
попадают только обезличенный итог, ссылки на локальные/CI evidence и честные
`NOT_RUN/BLOCKED` для недоступных проверок.
