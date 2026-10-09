# Playbook — фактическое состояние master

Обновлено 9 октября 2026 года после разрешённого переноса результатов эксперимента.
Рабочая ветка — master. vNext уже слит через [PR #9](https://github.com/ashishki/AI_workflow_playbook/pull/9);
его миграция не является текущей задачей. Прежняя записка сохранена побайтно в
[истории](history/STATUS.before-results-merge-20261009.md), вместе с границами её
технических и пользовательских наблюдений.

## Что опубликовано

- Действующие Engineering / Product / Shared и совместимые Governed-пути сохранены.
- [PR #11](https://github.com/ashishki/AI_workflow_playbook/pull/11) слит:
  `dcd40b9967be4dfbcf35498089bbe49e015008af`. В master вошли архив трёх настоящих
  Controlled Delegation раундов и поясняющая документация.
- [Что делали и зачем](../CONTROLLED_DELEGATION_RU.md),
  [архив](../../reports/delegation/README.md) и
  [итог третьего раунда](../../reports/delegation/2026-10-08-round3/REPORT_RU.md).
- Восстановлены два точных архивных pyc-файла, ранее проигнорированных Git;
  все 676 индексированных SHA256 проверены. Frozen отчёты и результаты не переписаны.

Перенос не включает рабочий runtime экспериментальной ветки, Delivery/Desktop
или автоматическое включение делегирования. Исходная feature-ветка ad55ee4
сохранена для harness и дальнейшего исследования.

## Наблюдённый вывод

В последнем раунде все шесть приложений исправили три причины сбоя и получили
100/100. При одинаковом качестве наблюдённых приложений C медленнее B в 1.46 раза;
uncached input выше в 2.93 раза, output — в 1.69 раза. Добавочная польза на этих
сценариях не показана. Один implementation-агент остаётся исходным вариантом;
существующие требования независимого review не отменяются.

Полная qualification BLOCKED: worker scope instructions нельзя проверить из
opaque payload, USD и активное время человека неизвестны. Ошибочные исходные
FAIL/STOP_SHIP сохранены; исправленная трактовка и связанные свидетельства прошли
настоящее повторное независимое review PASS. Два повтора одного среднего
синтетического проекта не доказывают production-пользу и не заменяют реальные пилоты.

## Проверки переноса

На точном head PR #11 `c10507f499667dec19ecaaf2616bf8582e40e9e3`:

- [Playbook vNext — PASS](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37895067097).
- [Native Product Checks — PASS](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37895067094).
- [Playbook Checks — FAIL](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37895067174):
  тесты не собираются без установленного ai_workflow_harness_lab.

Локально на подготовленном дереве: vNext 29 tests PASS, Native 24 tests с одним
root-permission skip, contracts/runtime sync/diff PASS. Ошибка full pytest и шесть
missing references старого pilot также воспроизведены на чистом f03dde86, до
переноса архива. Они остаются открытыми; старые или неполные проверки не выданы за PASS.

## Что остаётся

1. Отдельно исправить и проверить dev test setup, затем повторить полный suite.
2. Разобрать ссылки на исторические локальные pilot-свидетельства: сохранить
   факты и границы доступности, не выдумывать approval/reviewer results и не
   ослаблять действующие проверки ради зелёного статуса.
3. [Delivery PR #10](https://github.com/ashishki/AI_workflow_playbook/pull/10)
   остаётся draft и не слит; его программа и Desktop не получают приёмку из этого merge.
4. Настоящие Product-пилоты, внешнее использование и rollout остаются отдельной
   работой с применимыми правами. Три синтетических эксперимента не закрывают M5–M6.

Ветки docs и vNext уже входят в master; удаление веток не выполнялось. Локальный
master обновлён обычным fast-forward и проверяется относительно origin/master.
Текущий SHA нужно брать из Git, а не трактовать SHA исторического merge как
постоянный текущий head. Ни production-данные, ни установленные downstream не менялись.
