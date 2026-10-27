# Secret Access: инженерный эксперимент

Проверяем [практику](../../SECRETS_RU.md) и отдельно Relic. Не часть Product/Desktop.
Пакет готовит сравнение и отчёт; **он не запускает модели автоматически**, не
подключает аккаунты, не импортирует ключи и не принимает решение вместо владельца.
Python 3.11+ standard library. Для настоящих model runs использовать существующий
[Harness Lab](../../../companion/ai_workflow_harness_lab/README.md), не клонировать его.

## 1. Offline — можно сразу на VPS

Из корня чистой рабочей копии этой ветки:

```bash
python -m unittest discover -s engineering/experiments/secret-access -p 'test_*.py' -v
python engineering/experiments/secret-access/experiment.py prepare \
  --root .playbook-artifacts/secret-access/run-001 \
  --head "$(git rev-parse HEAD)" --host 'offline-only' --model 'not-used' --trials 1
python engineering/experiments/secret-access/experiment.py smoke \
  --root .playbook-artifacts/secret-access/run-001 --run B-1
python engineering/experiments/secret-access/experiment.py report \
  --root .playbook-artifacts/secret-access/run-001 \
  --output .playbook-artifacts/secret-access/report-001
```

Для проверки выбранного лога есть `scan --root RUN --run C-1 --path C-1/TRACE.json`.
Он ищет только известные искусственные значения/их base64 и split-представления;
не заменяет secret scanner и не читает весь home. Код 1 означает найденный canary.

Результат: искусственные inputs, A/B/C workspaces, plan.json, observations.json,
offline-receipt и REPORT_RU.md/results.json. Все живые наблюдения остаются NOT_RUN,
рекомендация — KEEP_EXPERIMENTAL. Нет имитации успешного Relic/model trial.
Секреты искусственные и не предоставляют доступа к сервисам. `smoke` намеренно
показывает, что программа с ключом может вывести/преобразовать/записать его; ничего
не отправляет по сети. Это negative control, НЕ средство защиты секретов.

## 2. Живой опыт — отдельный каталог после согласования

Прочитать [протокол](PROTOCOL_RU.md), зафиксировать реальную модель/версию host,
baseline, настройки, разрешения и бюджет; prepare с новыми root, head и trials=3.
Не использовать offline план для заявления о реальной модели. Получатся девять
полных проходов A/B/C в counterbalanced order из plan.json. Следовать всем 8 cases.

Разрешение на подготовку исходников не означает согласие на использование аккаунта.
Сначала провести сравнение A/B на искусственном локальном проекте. C блокируется,
пока нет отдельного disposable Relic project и разрешённого тестового login.

`synthetic_app.py` моделирует описанный владельцем способ, при котором приложение
само загружает `.env`: в тестовой fixture поддерживается только узкий формат
искусственных значений, а уже переданные переменные имеют приоритет. Это не описание
фактического кода конкретного проекта и не универсальный dotenv parser. До live
сравнения всё равно нужно наблюдать и зафиксировать настоящий baseline по протоколу.
При обычной загрузке повреждённый `.env` вызывает отказ и при наличии переменной.
В C необходимо использовать `--require-injected`: `.env` не читается и отсутствие
инъекции не маскируется запасным вариантом. Это условие нужно проверить по receipt.

## 3. Relic — сначала план, потом владелец

База документации: Relic 0.10.2, commit в [SOURCES.md](SOURCES.md). Проверить
фактическую версию, путь бинарника, источник и `--help` перед использованием.
Более новая версия не получает старые результаты автоматически. Установка только
с разрешения, без curl|sh и без изменения глобальной среды со скрытыми credentials.

```bash
python engineering/experiments/secret-access/experiment.py provider-plan \
  --root .playbook-artifacts/secret-access/live-001 --run C-1 \
  --binary /absolute/path/to/relic --project DISPOSABLE_PROJECT_ID
```

Команда ничего не запускает: показывает массивы аргументов. В Relic владельцу
нужно отдельно создать указанные тестовое environment `pbexp-...` и folder `probe`.
Запустить показанный `preview_import`, проверить plan. Только после явного согласия
выполнить `owner_confirmed_import` (без overwrite/delete). Не вставлять значения
в чат. Не считать сам вызов CLI достаточным подтверждением владельца.

После owner-import и проверки того, что проект исключительно тестовый:

```bash
python engineering/experiments/secret-access/experiment.py provider-smoke \
  --root .playbook-artifacts/secret-access/live-001 --run C-1 \
  --binary /absolute/path/to/relic --project DISPOSABLE_PROJECT_ID --consent-synthetic
```

Выполняются только `--version`, `check` и `run` fixed synthetic probe. Нет login,
создания ресурсов, импорта, удаления или arbitrary command. CLI может обращаться
к серверу Relic и использовать существующую авторизацию: это живой opt-in шаг.
Допустим только отдельный тестовый OS user/VM: harness НЕ ограничивает его доступы.
Результат проверяет JSON `ok`, а не один exit code. Необычный вывод оставляет FAIL
для разбора, а не «достаточно похоже». Сырой stdout не копируется в receipt.
MCP, synthetic_app.py и настоящий код приложения этот smoke НЕ проверяет.

## 4. Остальной цикл и отчёт

Cases conflict/fresh_session/second_machine/rotate_revoke/outage_exit/boundary
выполняются наблюдателем и агентом по протоколу: один CLI smoke их не заменяет.
Для missing использовать действительно отсутствующий ключ/окружение; для rotation —
import-v2.env, проверенный потребитель с ожидаемым v2, затем отказ v1. Не менять
замороженные fixtures. Дополнительные результаты складывать рядом, не перезаписывать.
Повторные smoke и результаты требуют нового каталога, чтобы не терять неудачи.

Заполнить observations.json метриками и ссылками на фактические receipts. SHA файла:
`python -c "import hashlib,pathlib; print(hashlib.sha256(pathlib.Path('RECEIPT').read_bytes()).hexdigest())"`.
Выполнить `assess --root RUN`, получить fingerprint; независимый reviewer после
проверки заполняет review. Затем `report --root RUN --output NEW_REPORT_DIR`.
Код отказывает при отсутствующей/изменённой evidence, неполные данные не становятся
PASS, offline результаты не дают рекомендацию внедрять.

Отчёт не копирует приватные логины, source `.env` или chats. До commit человек
проверяет REPORT_RU.md/results.json. Публиковать только безопасный итог и ограничения,
не `plan.json`, observations и весь run directory. Не коммитить `.playbook-artifacts`.

### Подготовка входа Harness Lab

После `prepare` можно создать совместимый suite в отдельном локальном каталоге:

```bash
python engineering/experiments/secret-access/lab_suite.py \
  --root .playbook-artifacts/secret-access/live-001 \
  --output .playbook-artifacts/secret-access/lab-live-001
PYTHONPATH=companion/ai_workflow_harness_lab/src python -m ai_workflow_harness_lab.cli \
  validate-suite .playbook-artifacts/secret-access/lab-live-001
python engineering/experiments/secret-access/lab_suite.py \
  --root .playbook-artifacts/secret-access/live-001 \
  --output .playbook-artifacts/secret-access/lab-live-001 --check
```

Это только подготовка: никакие модели и сервисы не запускаются. `schedule.json`
сохраняет порядок плана и сопоставляет A с `baseline`, B/C с `playbook`; запускать
нужно по одному `--task-id` в этом порядке. Счётчик receipt в suite проверяет только
наличие receipt, а не восемь cases, безопасность или пользу. Исполнитель и оператор
всё ещё должны обеспечить реальные изолированные сессии, наблюдения, все условия и
лимиты протокола, сбор доказательств и независимую оценку. Suite не выдаёт разрешений,
не фиксирует baseline и не обеспечивает контроль бюджета или изоляцию сам по себе.
Перед каждым запуском `--check` сверяет все копии, prompts, inventory, suite и schedule
с исходным планом и текущим builder; сохранить результат. Сам Harness Lab не соблюдает
`schedule.json`: оператор проверяет порядок и condition по каждому receipt. Как и
другие хеши в этом эксперименте, эта проверка не является независимой аттестацией.

## Ограничения механизма

Это экспериментальный helper, не production runner/secret scanner. Он использует
временные файлы для захвата вывода (только искусственные секреты в disposable среде),
ввод/права владельца и защиту ОС не заменяет. На Unix timeout завершает группу
процессов; на Windows зачистка потомков требует отдельной проверки. Никаких заявлений
о полном отсутствии plaintext на диске, математической изоляции или безопасном
произвольном коде с ключами. Тесты с fake CLI проверяют только этот harness.

Короткий запуск для агента: [VPS_PROMPT_RU.md](VPS_PROMPT_RU.md).
