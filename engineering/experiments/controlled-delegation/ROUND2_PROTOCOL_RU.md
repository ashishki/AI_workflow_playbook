# Controlled Delegation — второй раунд

Первый раунд и его failed repair заморожены. Этот раунд проверяет исправления и
сравнивает A/B/C на двух прикладных задачах, по два одинаковых повтора каждой пары
(12 основных прогонов). Порядок публикуется до модельных запусков. Дополнительные
диагностические прогоны не смешиваются с A/B/C.

## Исправление денег

Новый явный контракт: вход/выход — целые копейки, внешние суммы — decimal strings.
`money_exact.py` не использует float и не меняет старые артефакты. Проверяются все
старые precision/overflow reproductions и числа долей из неудачного repair, точная
сумма, стабильность порядка и ошибка пропорции менее копейки. Это изменение типа
денежного контракта объявлено до новых прогонов, а не ограничение старых inputs.

## Прикладные задачи и шкала

- Sales import: нормализация и точные деньги, immutable event IDs, повторный импорт,
  конфликт payload, откат всей пачки, детерминированный export, параллельные записи
  в SQLite. Семь наблюдаемых test groups, сумма весов 100.
- Release gate: три независимых источника, дубликаты/обновления/устаревшие и будущие
  записи, latency/incident/safety/cost ограничения. Семь групп, сумма весов 100.
  Ожидаемые данные доступны оператору, но не копируются в модельные workspaces.

Шкала и fixtures закреплены в `round2_fixtures.py` и `run-plan.json` до первого
запуска. Изменение protected input/test files даёт FAIL, а не рост score. Task PASS
требует score=100, структурированного STATE, завершённых host-сессий и пригодного
независимого code review, когда менялось приложение. Score задаёт оператор по
проверкам; модель не выставляет себе оценку.

## Равные условия

A — ordinary Codex; B — Playbook и один implementation/research session;
C — Playbook и 2–3 действительно полезных независимых read-only native workers.
Модель, reasoning, runtime flags, permissions, исходные task/data/test files,
порядок помощи и бюджеты одинаковы. B/C получают одинаковые skills. Один writer
владеет engine/decision/STATE; depth=1, max parallel=3. Finished worker не используется
повторно. До 60 секунд на worker внутри implementation budget. Reviewers не
запускаются внутри model task или worker.

Общий бюджет пары: 540 секунд, первый implementation host — максимум 300 секунд.
После code task оператор запускает свежий общий read-only Native Role Runner,
максимум 90 секунд, в копии без condition/chat/skills. Он получает реальные test
receipts. Для text-only решений дополнительного ceremonial review нет. Допускается
одна repair session с одинаковым порядком feedback; изменённый code требует новой
ограниченной проверки в остатке бюджета. Никакой repair не скрывает first attempt.

## Измерения и решение

Измеряется реальная длительность всех фаз, отдельные input/cached/output counters
main + native children + review + repair. Interrupted counters отмечаются partial.
USD без billing receipt — null/NOT RUN. Нельзя подменять их API price estimate или
считать ChatGPT subscription бесплатным запуском. Активное время человека без
его участия — null/NOT RUN; отсутствие обращений не равно нулю человеко-минут.

Оценка добавочной пользы: paired score, median wall и отдельные token ratios C/B
для каждого типа задачи, с раскрытием first attempts и retries. При двух повторах
вывод относится к этим двум задачам. Full qualification остаётся BLOCKED при
неизмеренных USD/human minutes, даже если отдельный task PASS. Это не разрешение
безусловно включать capability или production rollout.

Отдельно требуется настоящий native worker, которому дан старый GO-snapshot;
его реальный ответ должен противоречить текущему HOLD и быть отвергнут main.
Это controlled stale-input fault, не имитация ответа и не доказательство выявления
любой галлюцинации. Ещё один реальный model probe проверяет timeout/interrupt
невернувшегося worker; локальные unit timeout tests не заменяют этот probe.

## Команды

    python3 engineering/experiments/controlled-delegation/round2.py prepare --root .playbook-artifacts/delegation-round2/runs --head <prepared-source-SHA> --model gpt-6.1-sol --reasoning high
    python3 engineering/experiments/controlled-delegation/round2.py run --root .playbook-artifacts/delegation-round2/runs

Новые raw chats остаются локально. Публичный итог — отдельный
`reports/delegation/2026-10-08-round2/REPORT_RU.md`, `results.json` и receipts;
старый отчёт не переписывается. Master/production/аккаунты бизнес-сервисов не меняются.
