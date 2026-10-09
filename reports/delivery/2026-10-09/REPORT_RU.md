# Delivery: что проверено и что осталось

Дата наблюдений: 9 октября 2026. База master:
`de2478f4a3fdffb4c568898f37a078500f203b8a`. Рабочая ветка:
`feature/delivery-acceptance-20261009`, [PR #12](https://github.com/ashishki/AI_workflow_playbook/pull/12).
Проверенный runtime source commit: `7f36b90859a17c07f47197fed32e5fe1f4c8e1b3`.
Версия Native/Desktop: **0.2.0-preview.4**, private evaluation preview.

## Результат простыми словами

Исправлена сломанная общая проверка репозитория. Старые результаты сохранены,
а отсутствующие доказательства названы отсутствующими. Delivery source из PR #10
объединён со свежим master, включая последние Discover/Verify изменения.
Установщик проверяет свои файлы, расположение helper и журнал; потерянная,
изменённая или перенесённая установка останавливает изменения и требует разбора.
Рабочий пакет действительно собран и испытан, включая кнопки окна и браузер.

Создано новое локальное приложение на вымышленных данных. Оно сохраняет записи,
ограничивает выдачу выбранной демонстрационной личности, не создаёт дубль после
неизвестного сетевого исхода, восстанавливается из реальной копии и отключается
с читаемым экспортом. Проверены HTTP, браузер 390/1280 px и отдельный агент
продолжения без прежнего чата. Это техническая репетиция, не пилот преподавателя.

Полная программа D00–D10 **не принята**. Нужны настоящие люди/повторное использование,
разрешённый non-root model worker и бюджет для новых CLI/Lab прогонов, live
интеграции, owner Preview/Claim и чистые пользовательские машины. Выпуск не одобрен.

## Проверки исходников и CI

| Проверка | Статус | Фактический результат |
|---|---|---|
| Чистый dev virtualenv + editable Harness Lab | PASS | Python 3.12.13, install/import/pip check; package реально установлен |
| Full pytest на clean runtime commit 7f36b90 | PASS с двумя NOT RUN | 320 passed, 2 skipped, 17 subtests; пропуски перечислены ниже |
| Общий canonical verifier | PASS | required_failures=0; initializer/negative checks действительно выполнены |
| vNext | PASS | 50 tests, helpers/evidence/schema/поставка |
| Desktop | PASS | 20 tests; настоящие семантические regression failures на старом source сохранены |
| Native package без root | PASS | 24 tests; Unix permission assertion выполнен, skip отсутствует |
| Runtime sync и ownership contracts | PASS | canonical/bundled bytes совпадают; Discover/Verify master сохранены |
| Playbook Checks CI | PASS | [run 37903025549](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37903025549) на 7f36b90 |
| vNext CI Python 3.10/3.13 + Engineering | PASS | [run 37903025451](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37903025451) на 7f36b90 |
| Native/Package/Desktop CI Windows/macOS/Linux | PASS | [run 37903025448](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37903025448) на 7f36b90 |
| Historical CLI 0.144.4 permission probe | NOT RUN | установлен 0.160.1; pinned identity не подменялся |
| Historical frozen host match | NOT RUN | исторические пути/байты отсутствуют; нынешний VPS не назван старым host |
| July approval/run/adjudication primary evidence | NOT RUN | оригиналы отсутствуют; [доступность](../../../docs/evaluation/TEST_FIRST_PILOT_EVIDENCE_AVAILABILITY.md) |

[D00 report](D00_REPORT_RU.md) описывает archive anchors 179/119 файлов,
фактически исправленные dev/sandbox ошибки, strict collection refusal и сохранённые
начальные FAIL. Текущий live-builder старого pilot по-прежнему отвергает drift;
archive PASS подтверждает только source integrity, не прошлую execution authority.
Отсутствующая Git-история — явная ошибка доступности, не скрытый skip.

## Поставка и настоящий интерфейс

На чистом tracked source 7f36b90 получен новый Linux frozen ZIP:
`Playbook-Desktop-0.2.0-preview.4-linux-x86_64.zip`, SHA256
`4a5e4afa7a46ba786a604ae3fc0702b4856fde24a419fbbb4c7a737e988b7f33`.
Локальный файл находится в
`.playbook-artifacts/delivery-acceptance-20261009/desktop-final/accepted-bundle/`.
Полный состав проверен по DESKTOP manifest. Embedded Native ZIP, helper identity
и отдельная новая canonical сборка совпали:
`cf348a2008dfbd808ad3146ced869436ee634062ccde8b3665a1497cc1d5ab32`.
SHA tracked source до/после всех этих проверок совпали.

Выполнены настоящие install → doctor → update → stored helper invocation →
remove → rollback. Preview.5 для update — явно синтетический следующий kit,
не выпущенная версия. Проверены запрет downgrade, изменённые owner файлы,
отсутствующий/подменённый pointer, lost journal и copied/moved project. Отказы
сохраняют все файлы; owner notes, AGENTS и .gitignore проверены побайтно.
GUI запускался под Xvfb: реальные Tk buttons/dialogs, interrupted/pointer diagnoses,
восстановление/удаление. Снимки просмотрены. Это Linux VPS automation, не человек
на чистой машине. Rollback установки не выдаётся за backup данных приложения.

Распакованный START.html прошёл настоящий Chromium/Playwright 1.61.1: 48 комбинаций,
clipboard/fallback, сценарии, пустой ввод и 390/1280 px. CI также собрал и проверил
настоящие Windows x86_64, macOS arm64 и Linux x86_64 ZIP/self-test/browser.
[Состав и hashes скачанных CI artifacts](evidence/ci/artifacts.json) проверены
по полученным байтам. Другие архитектуры, чистые машины, OS signing/notarization,
реальный login/reviewer на каждой ОС — NOT RUN. Artifacts сохранены локально;
CI retention 7 дней, постоянная дистрибуция не создана.

## Сквозная синтетическая репетиция

Критерии и первоначальные файлы закреплены [до agent work](evidence/journeys/plan.json).
Исполнитель получил копию Native skill из source 2225a3f и конкретные правила от
сопровождающего. Это platform collaboration agent с действительными файловыми
изменениями и командами; **не Native CLI/Lab empirical pair**. Полный product
review loop/NO-CODE выбор этим заданием не измерены. Source runtime на финальном
7f36b90 проверялся отдельно. В первоначальной skill-копии нет frontend skill;
browser acceptance независимо выполнил основной агент.

- [Первоначальное приложение](outputs/initial-app/PROJECT.md): 13 local tests PASS,
  реальные HTTP/lifecycle observations. Данные, имена и роли вымышлены.
- Внешний HTTP checker: 10 групп PASS — identity/header spoof, list/id isolation,
  повтор request_id, conflict, real date/time validation, concurrency 8, restart,
  backup/corruption/restore, export/retire, исходные owner файлы.
- Отсутствующая/повреждённая backup: фактический restore rc1, данные побайтно
  сохранены. Это PASS безопасного отказа, не PASS восстановления.
- Настоящий браузер: 6 групп PASS. Создание и ошибка в UI, смена личности,
  mobile width, строка с HTML отображается текстом, reload и потеря response
  **после реального committed POST** с повтором прежнего id без дубля.
  Скриншоты просмотрены; полезность и удобство для человека не измерены.
- Первый browser probe — FAIL из-за неверного ожидания видимости пустого status
  элемента. Ошибка checker, не приложения; старый probe/log сохранён отдельно.
  Исправлено ожидание фактически загруженного списка, приложение не менялось.
- Fresh transfer: отдельный агент с `fork_turns=none`, только файлы проекта и новая
  конкретная просьба. 16 local tests PASS, внешний HTTP/CLI checker — 5 групп PASS:
  новые 09:45 отклонены, 09:30 приняты, старые 09:15/read/retry/restore сохранены.
  Исходные данные и инструкции не изменились. Учтено одно вмешательство координатора:
  пояснение cache-free copy/baseline/log preservation, без прежнего чата или бизнес/код
  подсказки. Первые две ошибки inherited checks
  (generated cache baseline и readiness ожидание) и их исправления сохранены; это
  не подмена старого execution outcome. [Новая запись](outputs/transfer-app/TRANSFER_RESULT.md).

Финальный reviewer выявил ещё два P2 именно в наблюдённых прототипах: ошибка
fsync после состоявшегося rename оставляла старый cache, и следующая запись могла
стереть уже committed запись; retire с output именем служебного marker затирал
свой JSON export. Старые source/PASS сохранены. Исправленный follow-up создан
отдельно: [corrected-app](outputs/corrected-app/CORRECTION_RESULT.md), app SHA256
`82d0417f3fab4923e82e768bf5121ba60dfc2f6c4519195544bf7e8bcf291788`.
Реальная RED на прежнем source: 14 failures в 7 новых методах; final GREEN:
24 tests (16 прежних + 8 fault/metadata regressions). Cache сверяется с actual
validated disk после write failure; недоступный reload блокирует дальнейшие операции.
503 сообщает неизвестный исход и прежний request_id. Служебные export names
отклоняются до изменений. Внешний HTTP/CLI checker новой копии: 5 групп PASS; browser — 6 групп PASS,
390/1280 screenshots просмотрены. Дополнительный checker timing FAIL при async
refresh списка сохранён; исправлено ожидание ответа UI, app source не менялся.
Тот же независимый reviewer подтвердил real fsync/replay/next-write/fail-closed и
9 reserved-path CLI refusals, 24 tests PASS: [recheck](evidence/review/prototype-recheck.json).

Неполная published copy первоначально не содержала .agents — отдельный P2 архивирования.
Восстановлены точные наблюдённые skills; initial также содержит доступный оригинальный
pyc, проверенный против recorded SHA. Baselines не ослаблены, ошибки reconstruction
сохранены. Независимые temp copies: 13/16 checks PASS. На ещё одной root temp copy
initial получен один startup/SIGINT timing FAIL из 13; старый source/test оставлен
как исторический, flake не скрыт. Transfer helper ждёт actual HTTP readiness;
полная corrected published copy: 24 PASS. [Как повторять](REPLAY_RU.md).

Две локальные demo identities не являются production authentication: любой
посетитель может выбрать другую личность. Проверена серверная выдача по заданной
identity, не защищённый вход двух настоящих пользователей. Сервер bind localhost;
публичная ссылка и внешняя отправка отсутствуют. Retire относится только к локальной
копии; внешних jobs/subscriptions нет, их отмена не заявляется.

## Приёмка программы и следующие действия

| Шаг | Полный статус | Что наблюдалось / чего не хватает |
|---|---|---|
| D00 | PASS для переносимой основы | Полные source checks + exact CI; два historical host probe остаются NOT RUN |
| D01 | PASS для inventory capability | Read-only CLI и negative tests; missing Wrangler/live auth не скрыты; готовность accounts не заявляется |
| D02 | NOT RUN целиком | Текущий реальный repo change + initializer/regressions; нет трёх real Engineering CLI проходов по протоколу |
| D03 | NOT RUN целиком | APP synthetic HTTP/browser PASS; NO-CODE owner story и разрешённый публичный preview не пройдены |
| D04 | PASS для локального technical transfer | Stale/missing/external refs выявляются; fresh-agent change прошёл внешний HTTP/CLI checker; human transfer не наблюдался |
| D05 | PASS для локальной disposable recovery | Backup действительно восстановлен; unknown HTTP outcome безопасен; внешняя интеграция отдельно |
| D06 | NOT RUN целиком | Local identities/concurrency/export/off-state PASS; live Preview/Claim/account/real roles не приняты |
| D07 | NOT RUN | AI/retrieval/API fresh observations/independent labels отсутствуют; offline fixtures не названы live |
| D08 | NOT RUN целиком | Независимый platform source review/fix/recheck; Native exec/plain paired comparison и полные counters отсутствуют |
| D09 | NOT RUN | Нет выбранного реального участника, разрешённых примеров и позднего возвращения |
| D10 | NOT RUN целиком | ZIP + Linux lifecycle + matrix CI PASS; field use/clean-machine/rights/release decision открыты |

Первый незавершённый полный шаг после D01 — D02: non-root worker с разрешёнными
model/provider и бюджетом; его авторизация не копируется с root. Старое root exception
разрешало ровно шесть R3 runs, не новый Delivery batch. Запрос участника/рабочего
примера отправлен владельцу; ответа на момент записи нет. До этого невозможно
честно назвать pilot завершённым или симулировать недельный повтор.

Для внешнего Preview/Claim нужен конкретный согласованный безопасный результат,
согласие на временную публичность, owner account и Terms/Privacy. Эти действия
не следуют из разрешения git merge. Затем отдельный чистый Desktop trial на трёх
ОС и решение владельца о выпуске/правах.

## Независимое review, стоимость и польза

[Первоначальные результаты](evidence/review/initial.json) сохранены отдельно от
последующего recheck. D00 reviewer нашёл два P2 sandbox invocation/copy identity;
исправления внёс основной исполнитель, reviewer оставался read-only.
Предварительный Desktop audit выявил pending-journal false green и missing/tampered
runtime pointer. Новый reviewer обнаружил неправильную managed command и bypass
journal identity при mutation. Confirmed defects исправлены и соответствующие
реальные checks повторены. Финальный verdict после отчёта/ZIP/CI учитывается в
[отдельном final review](evidence/review/final.json); platform evidence не маскируется под Native Role Runner.

Независимый review оказался полезен здесь: обнаружил конкретные пропуски
исполнителя. Это не доказывает преимущество C над B в Controlled Delegation.
[Сохранённые R3 результаты](../../delegation/2026-10-08-round3/REPORT_RU.md): одинаковое
качество 100/100, C/B wall 1.46, uncached input 2.93, output 1.69; добавочной пользы C
на этом сценарии не показано. Один implementation agent + нужный независимый review
остаётся практическим исходным вариантом. Дальше сравнивать новые реальные задачи
и полную цену, без автоматического включения делегирования всем проектам.

Новых Codex CLI/API inference runs в этой Delivery проверке: **0**. Platform
implementation/review/transfer agents реально работали; их tokens/model billing
и основной сессии не доступны. **Общая USD стоимость unknown, не $0**. Human active
minutes и цена compute/GitHub Actions unknown. Новые аккаунты/подписки/paid trials
не создавались. Отдельная plain/control пара не выполнена, новой cost/quality
победы не заявляется.

Машинный итог: [results.json](results.json). Logs/receipts сохранены с фактическими
argv, timestamps, exit codes, source SHA и stdout/stderr digests. Старые FAIL не
переписаны. Merge source/docs не обновляет установленный downstream, не включает
Controlled Delegation автоматически и не означает production/release approval.
