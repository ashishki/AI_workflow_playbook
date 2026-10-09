# Что получилось во втором раунде

Два одинаковых повтора A/B/C на двух задачах: импорт продаж в SQLite и решение о выпуске релиза. A — обычный Codex, B — Playbook в одной implementation session, C — Playbook с 2–3 настоящими помощниками. Модель `gpt-6.1-sol`, reasoning `high`; порядок, исходные файлы и шкала закреплены до запусков.

На этих задачах добавочная польза делегирования не показана: медиана полного времени C выше B в 1.29 раза на импорте и в 1.44 раза на решении о релизе. Эти времена включают разные результаты приёмки, поэтому они не доказывают ускорение успешной работы.

**Решение: REVISE_OR_REJECT. Полная квалификация: BLOCKED.** Фактические USD и активные человеко-минуты не измерены и остаются `null / NOT RUN`. Делегирование не становится режимом по умолчанию.

## Результаты задач

| Задача | A | B | C |
|---|---|---|---|
| sales_import | 2 PASS | 1 FAIL, 1 PASS | 1 BLOCKED, 1 FAIL; protocol FAIL: 1 |
| release_gate | 2 PASS | 2 PASS | 2 PASS |

Task PASS требует score=100, STATE, завершённого host и пригодного независимого review изменённого приложения. BLOCKED означает недостающую проверку, включая отсутствующий/timeout QA, и не доказывает неправильность кода. Для текстового решения о релизе дополнительный review не требуется. Исходный collector label сохранён отдельно.

## Время и токены

| Задача | Median A, с | Median B, с | Median C, с | C/B wall | C/B uncached input | C/B output |
|---|---:|---:|---:|---:|---:|---:|
| sales_import | 299.93 | 221.86 | 286.65 | 1.29× | 1.10× partial | 1.10× partial |
| release_gate | 140.16 | 153.56 | 220.83 | 1.44× | 2.27× | 1.52× |

Wall включает implementation, реальные проверки, review и repair. Меньше 1× — меньше времени/токенов C. Input включает cached; uncached=input−cached. Суммы ниже включают доступные counters main, отдельных native children, reviews и repairs. Неизвестные counters не считаются нулём. Partial counters — нижняя наблюдаемая граница, а не полный расход. Partial ratio не доказывает меньшего полного расхода C. Время неуспешного/непроверенного решения не доказывает ускорение успешной работы.

| Задача / режим | Input | Cached input | Output | Counters |
|---|---:|---:|---:|---|
| sales_import / A | 689661 | 560128 | 15252 | complete |
| sales_import / B | 541386 | 442112 | 11582 | complete |
| sales_import / C | 760727 | 651904 | 12697 | partial / incomplete |
| release_gate / A | 324825 | 275200 | 8475 | complete |
| release_gate / B | 412656 | 326016 | 10269 | complete |
| release_gate / C | 872518 | 676224 | 15582 | complete |

Токены не названы денежной стоимостью; API price estimate не заменяет billing receipt. Отсутствие обращений к владельцу не означает ноль активных человеко-минут. При двух повторах вывод ограничен этими задачами.

## Первые попытки и исправления

| Задача / режим / повтор | Первая приёмка | Первый score | Первый review | Исправления | Итог задачи |
|---|---|---:|---|---:|---|
| release_gate / B / 2 | PASS | 100 | NOT_REQUIRED | 0 | PASS |
| release_gate / C / 2 | PASS | 100 | NOT_REQUIRED | 0 | PASS |
| release_gate / A / 2 | PASS | 100 | NOT_REQUIRED | 0 | PASS |
| sales_import / C / 2 | FAIL | 100 | STOP_SHIP | 1 | BLOCKED |
| sales_import / A / 2 | FAIL | 100 | STOP_SHIP | 1 | PASS |
| sales_import / B / 2 | PASS | 100 | PASS | 0 | FAIL |
| sales_import / B / 1 | FAIL | 100 | STOP_SHIP | 1 | PASS |
| sales_import / A / 1 | FAIL | 100 | STOP_SHIP | 1 | PASS |
| sales_import / C / 1 | PASS | 100 | PASS | 0 | FAIL |
| release_gate / C / 1 | PASS | 100 | NOT_REQUIRED | 0 | PASS |
| release_gate / A / 1 | PASS | 100 | NOT_REQUIRED | 0 | PASS |
| release_gate / B / 1 | PASS | 100 | NOT_REQUIRED | 0 | PASS |

## Одинаковая дополнительная проверка

После основных прогонов всем шести замороженных приложений импорта дана одна и та же допустимая сумма `1e5000`: импорт, повтор и точный вывод. Проверка выполнялась в копиях. Она раскрывает наблюдённый независимым QA дефект лимита цифр и его пропуски; это дополнительная проверка после основных запусков, исходные score/rubric/receipts не изменены.

| Режим / повтор | Приёмка по исходной процедуре | Доп. проверка контракта | Итог задачи |
|---|---|---|---|
| C / 2 | BLOCKED | PASS | BLOCKED |
| A / 2 | PASS | PASS | PASS |
| B / 2 | PASS | FAIL | FAIL |
| B / 1 | PASS | PASS | PASS |
| A / 1 | PASS | PASS | PASS |
| C / 1 | PASS | FAIL | FAIL |

Итог задачи учитывает подтверждённое нарушение контракта из этой дополнительной проверки. PASS независимого модельного проверяющего не доказывает отсутствия такого дефекта. [Полный receipt](evidence/posthoc-large-decimal.json).

Первый STOP_SHIP/timeout не скрыт последующим repair. First-checks и исходные receipts сохранены отдельно; у старого поля `first_attempt_status` в raw receipt более узкий смысл — implementation+mechanical check.

## Проверки помощников

- stale_advice: **PASS**. [Receipt](evidence/diagnostic-stale_advice.json).
- worker_timeout: **PASS**. [Receipt](evidence/diagnostic-worker_timeout.json).
- sales_import/C/1: **protocol FAIL**, worker exceeded 60-second bound: 01a11bde-1605-7a13-a26f-161c6b47169d (64.085 seconds).

Stale probe даёт настоящему worker старый GO-снимок и проверяет реальный конфликт с текущим HOLD. Это controlled stale-input fault, а не доказательство обнаружения любой галлюцинации. Timeout probe проверяет реальный interrupt настоящего native worker. Workers получили read-only инструкции; их sandbox наследуется от main, отдельная OS-изоляция от записи этим раундом не доказана.

## Что исправлено и что остаётся

Деньги переведены на явный новый контракт: целые копейки и decimal strings, без float. Regression tests проверяют старые precision/overflow cases и числа долей из failed repair. Дополнительно исправлено форматирование принятых сумм больше 4300 цифр без изменения глобального лимита Python. Это source fix после batch: замороженный helper и generated code прогонов не подменены. Collector теперь учитывает первый QA, отделяет missing QA от дефекта и отклоняет наблюдённый worker interval больше 60 с. Первые failed outputs и отчёт первого раунда заморожены. Бюджеты: implementation 300 с, worker 60 с, весь run 540 с, максимум одна repair; независимый общий review привязан к SHA проверенной версии приложения.

Результаты описывают эти синтетические задачи и конкретную среду. Успешные задачи и диагностические пробы не разрешают production rollout и не заполняют неизвестные USD/человеко-минуты. Для решения о включении нужны эти измерения и более широкий опыт.

Подробные paired scores, отдельные actual input/cached/output counters, thread/settings/usage, first attempts и review verdicts: [results.json](results.json). Индекс sanitized receipts: [evidence-index.json](evidence-index.json). Raw chats остаются локально: `/srv/openclaw-you/workspace/AI_workflow_playbook/.playbook-artifacts/delegation-round2/runs`.

## Исходники и независимая проверка

Реальный независимый source review дал **STOP_SHIP**: обработка внешнего QA timeout, приоритет matching/stale verdict и partial counters. Следующие ограниченные проверки нашли unsafe default binding и зависимость final hash-binding от вердикта. Все подтверждённые findings исправлены и покрыты регрессиями. Последняя настоящая read-only проверка дала **PASS только для final caller, helper и интеграционной регрессии**; это не полная повторная проверка всего дерева. [Полная цепочка, scopes, hashes и counters](source-validation.json). Все три STOP_SHIP сохранены.

Операторские проверки: vnext **86 PASS**, Native package **24 tests, 1 skip** (root обходит Unix read-only permissions), Role Runner **7 PASS**, vnext_check и runtime sync **PASS**. Desktop: **12 tests, 1 ERROR** — отсутствует `tkinter`; установка и зелёный результат не выдуманы. [Actual receipts](evidence/source-checks.json). Source reviews и diagnostic probes не смешаны с A/B/C token totals.
