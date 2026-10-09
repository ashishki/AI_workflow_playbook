# Playbook — текущая работа и фактические границы

Обновлено 9 октября 2026. Рабочая ветка: `feature/delivery-acceptance-20261009`,
база master `de2478f4a3fdffb4c568898f37a078500f203b8a`. Перенос в master учитывается
после фактического merge; downstream и production не обновляются этим кодом.

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

D00: 296 PASS / 2 explicit historical NOT RUN до последних sandbox corrections;
canonical после corrections PASS, независимый reviewer нашёл два P2 и повторно
подтвердил их исправление. Native package: 24 PASS без root и без permission skip.
[Точные receipts и ограничения](../../reports/delivery/2026-10-09/D00_REPORT_RU.md).
CI нового коммита и итоговая приёмка Delivery фиксируются после наблюдения.

## Что остаётся открытым

Полные реальные пользовательские истории, field-пилот, live AI/data integration,
Preview → Claim с owner account/Terms, чистые машины Windows/macOS/Linux и release
approval пока не подтверждены. Техническая автоматизация, fake CLI и синтетический
пример не закрывают эти пункты. Новые model CLI runs требуют non-root worker,
согласованного provider/model/budget; старое root exception относилось к шести R3
прогонам и не переносится на Delivery. Credentials не копируются.

Для реального пилота нужен участник и конкретный разрешённый рабочий пример,
затем настоящее повторное использование/изменение в более позднюю дату.

## Вывод эксперимента по делегированию

[Архив](../../reports/delegation/README.md) сохранён. В R3 при одинаковом качестве
всех шести результатов C медленнее B в 1.46 раза; uncached input выше в 2.93 раза,
output — в 1.69 раза. Добавочная польза на этих сценариях не показана. Один
implementation-агент остаётся исходным вариантом; независимый review сохраняется.
USD и время человека неизвестны, qualification BLOCKED. Новая Delivery-проверка
не превращает эти результаты в доказанную production-пользу.
