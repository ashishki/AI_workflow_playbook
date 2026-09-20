# VPS: выполнить проверки новой ветки и довести программу

Для владельца и следующего Codex-исполнителя. Эти команды подготовлены, **не
являются журналом уже выполненных проверок**. Текущая очередь — [D00–D10](PLAN_RU.md).
Используйте непривилегированного пользователя, отдельный checkout/одноразовые
рабочие копии и разрешённую среду. Не используйте реальные данные в fault injection.

## A. Исходники и полная среда (D00)

Получите `feature/playbook-delivery-20260920` обычным git fetch/switch. Перед
переключением сохраните чужие незакоммиченные изменения; не делайте reset --hard.
Из корня checkout:

```bash
git status --short
git branch --show-current
git rev-parse HEAD
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pip check
.venv/bin/python -c "import ai_workflow_harness_lab; import pytest; import jsonschema"
```

Создайте новый, не использовавшийся каталог evidence:

```bash
mkdir -p .playbook-artifacts
RUN="$(mktemp -d "$PWD/.playbook-artifacts/delivery-XXXXXX")"
git rev-parse HEAD > "$RUN/source-head.txt"
git diff --binary > "$RUN/local-changes.patch"
.venv/bin/python -m pip freeze > "$RUN/python-packages.txt"
.venv/bin/python --version > "$RUN/python-version.txt"
```

Не коммитьте полный evidence по умолчанию: проверьте приватность и используйте
защищённое хранилище. Каждый новый attempt получает новый каталог, включая failures.
Через **существующий** receipt_run выполните проверки ниже. Команды запускать
отдельно, фиксируя nonzero, а не прекращать отчёт на первом неуспехе:

```bash
.venv/bin/python tools/receipt_run.py --task-id D00-pytest --output-dir "$RUN/pytest" --timeout 1800 -- .venv/bin/python -m pytest -q
.venv/bin/python tools/receipt_run.py --task-id D00-canonical --output-dir "$RUN/canonical" --timeout 1800 -- .venv/bin/python tools/verify_playbook.py --root .
.venv/bin/python tools/receipt_run.py --task-id D01-vnext --output-dir "$RUN/vnext-tests" --timeout 600 -- .venv/bin/python -m unittest discover -s tests/vnext -v
.venv/bin/python tools/receipt_run.py --task-id D01-native --output-dir "$RUN/native-tests" --timeout 600 -- .venv/bin/python -m unittest discover -s evals/native -p 'test_*.py' -v
.venv/bin/python tools/receipt_run.py --task-id D01-package --output-dir "$RUN/package-tests" --timeout 600 -- .venv/bin/python -m unittest discover -s distribution/native -p 'test_*.py' -v
.venv/bin/python tools/vnext_check.py --root .
.venv/bin/python distribution/native/sync_runtime.py --check
.venv/bin/python -m ai_workflow_harness_lab.cli validate-suite evals/native/harness
git diff --check
```

Root пользователя нельзя использовать как доказательство Unix read-only permissions.
Причины skipped явно записать. Если после исправленного импорта обнаружатся
другие ошибки, воспроизвести и исправить их по существу; frozen results не править.
Не менять PYTHONPATH/allowlists/тестовые ожидания ради скрытого обхода проверки.
Канонический verifier и полный pytest не заменяются одним выбранным subset.

## B. Среда пользователя и фактическая поставка (D01/D03/D10)

```bash
.venv/bin/python tools/playbook_environment.py --root . --audience engineering --playbook-source --need tests --json
.venv/bin/python tools/playbook_environment.py --root . --need review --need browser --json
.venv/bin/python distribution/native/build.py --output "$RUN/kit"
```

Inventory с `--need` возвращает 1, пока execution checks остаются неизвестными.
Это **не** fail всей программы и не повод ослаблять checker. Отдельно подтвердить
дочерний reviewer и браузер. Не вводить «approved» флаг, который просто заменит эти пробы.

Распаковать новый ZIP в отдельную папку с пробелами/кириллицей, сверить checksum
и manifest, запустить helper из поставки, проверить новую сессию/discovery и
connect/update/remove с пользовательскими изменениями. Builder использует hard
links: на ФС без них сборка может не поддерживаться; определить границу или
добавить проверенный fail-safe путь, не обещать все файловые системы.

Браузер: используйте уже доступный инструмент. Для существующего CI probe:

```bash
# После разрешённой установки зафиксированного в CI Playwright/Chromium:
# PLAYBOOK_EVAL_PLAYWRIGHT_MODULE должен указывать на фактический модуль.
node evals/native/check-launcher.cjs "$RUN/browser" /absolute/path/to/extracted/Playbook/START.html
```

Просмотреть изображения. Проверять 390/1280 px, реальное основное действие,
ошибку, клавиатуру и текущую версию приложения. Скриншоты START проверяют справку,
не приложение, созданное владельцем. Браузер на VPS не доказывает desktop setup
на Windows/macOS. Настоящие среды остаются отдельными строками приёмки.


## B2. Временный внешний preview без DevOps-ритуала (D03/D06)

Это **разрешённая внешняя публикация временного preview**, поэтому её нельзя
запускать только потому, что `cloudflared` установлен. Используйте тестовые или
санитизированные данные. Не передавайте через Quick Tunnel приватные клиентские
данные, credentials, admin-интерфейсы или другой чувствительный контент.

Предварительно:

```bash
command -v cloudflared
cloudflared --version
```

Наличие команды не означает разрешение открыть публичный URL. Сначала запустите
собственный тестовый web-процесс на известном localhost-порту и проверьте его
локально. Зафиксируйте PID/порт и отличительный признак текущей версии.

После явного разрешения владельца:

```bash
# Пример; используйте фактический проверенный порт своего процесса.
cloudflared tunnel --url http://localhost:8000
```

Не парсите заранее выдуманный URL. Возьмите фактический адрес из stdout/stderr
процесса `cloudflared`; формат hostname может меняться. Проверка считается
выполненной, только если:

- tunnel процесс создан именно этой сессией и направлен на проверенный localhost;
- полученный HTTPS URL действительно отвечает;
- через внешний URL пройден безопасный основной сценарий текущей версии;
- пользователь видит пометку **«временный публичный preview»**, а не production;
- зафиксировано, что Quick Tunnel не предоставляет отдельную аутентификацию;
- после проверки Playbook останавливает только созданный им tunnel/process и
  сообщает, что ссылка не является стабильным адресом приложения.

Негативные проверки: неправильный порт, уже занятый/чужой локальный сервер,
отсутствующий `cloudflared`, tunnel startup failure, внешний URL не отвечает,
локальная версия и удалённая версия не совпадают, попытка использовать реальные
чувствительные данные. Ни одну из них не превращать в «preview готов».

Для продукта отдельно замерить путь нетехнического пользователя:
«попросил показать → подтвердил публичность → открыл ссылку на телефоне/у коллеги».
Количество команд Cloudflare, которые пришлось объяснить пользователю, должно быть
нулевым: внутреннее устройство остаётся механизмом Playbook.

Quick Tunnel не закрывает D10. Для постоянного использования нужен отдельный
deployment/ownership/access путь. Будущий claimable preview через Cloudflare
Temporary Accounts исследовать отдельно; не смешивать его evidence с Quick Tunnel.

## B3. Preview → Claim ownership для совместимого Worker (D03/D06)

Это реальное внешнее создание временного Cloudflare account/resource. Выполнять
только после явного разрешения владельца и на синтетическом/безопасном проекте
до пользовательского пилота.

### Изоляция

Wrangler хранит temporary account/token/claim values в глобальной конфигурации
текущего OS user. Не использовать общий profile нескольких пользователей и не
выполнять `wrangler logout` в обычном profile ради temporary flow. Для VPS —
отдельный непривилегированный OS user или другой проверенно изолированный context.

```bash
wrangler --version
```

Если Wrangler отсутствует, установка/обновление — отдельное разрешённое действие.
Наличие `npx` не считается установленным adapter: оно может скачать пакет.

### Acceptance run

До deployment владелец видит Cloudflare Terms of Service и Privacy Policy и явно
их принимает. Агент не выставляет acceptance молча.

На совместимом одноразовом Worker:

```bash
wrangler deploy --temporary
```

Успех требует фактически наблюдать:
- temporary account created/reused именно в изолированном context;
- live Worker URL;
- claim URL и expiry;
- live URL проходит заранее заданный безопасный smoke/acceptance scenario;
- claim URL не попал в Git, публичные artifacts, screenshots или shared logs;
- evidence хранит только безопасные признаки: received=yes, expiry, Worker URL,
  version/HEAD и при необходимости hash/redacted claim identifier, не полный URL.

### Claim

Claim завершает сам владелец в браузере в пределах claim window. Простое открытие
claim URL не считается завершением. После claim через отдельно разрешённый
Cloudflare path проверить, что supported resources остались в claimed account.

Отдельно проверить ownership boundary: claim не предоставляет Playbook permanent
write access. Следующий deploy либо получает обычную owner authorization, либо
честно останавливается.

### Negative cases

- Wrangler старее поддерживаемого temporary flow;
- текущий profile уже авторизован и `--temporary` отклонён;
- Terms/Privacy не приняты;
- temporary account creation/rate/abuse check отказал;
- unsupported resource;
- claim URL истёк;
- claim URL открыт, но dashboard claim не завершён;
- temporary resource исчез после non-claim;
- агент пытается логировать claim URL/API token;
- solution не подходит Workers temporary accounts.

Не обходить это автоматическим logout, переносом credentials, ослаблением sandbox
или объявлением production success.

Для будущего REST adapter отдельно проверить proof-of-work, server-side temporary
apiToken, user-scoped claim URL, отсутствие секретов во frontend/telemetry и
удаление temporary credentials не позднее expiry.

## C. Сквозные истории (D02–D07)

Сначала адаптируйте истории к безопасным реальным или явно синтетическим данным.
Зафиксируйте критерии до прогона, а внешние контрольные случаи не давайте
исполнителю. Таблица — задания/критерии, не готовые fixtures или выполненные tests.

| ID | Задание | Что нельзя пропустить | Проверяющий результат |
|---|---|---|---|
| ENG-NEW | Начать новый реальный инженерный проект | План и архитектура по риску, действующий framework, критерии, review, continuity | Работающий результат и список ручных вмешательств автора |
| ENG-CHANGE | Продолжить текущий проект с чужими локальными изменениями | Не запускать initializer заново; не менять pinned contracts; сохранить изменения | Новое правило и старые сценарии проходят |
| ENG-EXP | Сравнить один новый подход отдельно | Одинаковая база/задача, бюджет, не менять downstream, сохранить проигрыши | Воспроизводимый результат с границами, не универсальный совет |
| NO-CODE | У заявок нет следующего действия; имеющаяся таблица уже подходит | Не создавать CRM/AI без причины; правила определяет владелец | Рабочее изменение и возможный ручной способ |
| APP | Небольшая запись/заявка с UI и сохраняемыми данными | Не заглушка, мобильный/широкий экран, повтор нажатия, restart/persistence, ошибки | Данные сохранены, главное действие выполнено; оценка UX отдельно |
| TRANSFER | Новый агент в новой сессии меняет реальное правило | Нет старого чата; старые данные сохраняются; неизвестные права не наследуются | Новый агент выполняет изменение и проверяет старое поведение |
| RECOVER | Сломать безопасную копию интеграции/данных | Различать failed/unknown outcome, не повторять отправку вслепую; backup реально доступен | Данные восстановлены и путь работает либо честный blocker |
| GROW | Личное решение начинают использовать два человека | Не только добавить второй login: роли, изоляция, concurrency, ownership, стоимость | Раздельный доступ и проверенный предел нагрузки |
| RETIRE | Отключить или заменить решение на копии | Читаемый экспорт, jobs/connections, сохранность, не притворяться отменённой подпиской | Подтверждённое off-state в оговорённой среде |
| AI-EVAL | Помощник по безопасному корпусу документов | Answer/no-answer/conflict/stale/permission; правильность меток не от самого автора ответа | Реальные observations, раздельные retrieval/answer failures |

Добавьте чистые случаи без дефектов для выявления ложных замечаний. Реальные
интеграции разрешаются отдельно; их имитация не получает статус live. Не нужно
создавать отдельную тестовую платформу: используйте существующий Harness Lab,
проектные проверки и минимальные необходимые адаптеры.

## D. Независимые агенты через exec (D08)

До вызовов владелец задаёт допустимый бюджет, список разрешённых провайдеров и
моделей. Выбирайте минимальную достаточную стоимость **по качеству задачи**, а
не по уверенности дешёвой модели. Общая основная конфигурация не переписывается.
Модельные прогоны не запускаются от root и не получают production credentials.

Подготовьте краткий фактический request из [шаблона](REVIEW_REQUEST.md): задача,
HEAD/дифф/дерево, требования, изменённые файлы, результаты, известные ограничения.
Не подсказывайте требуемый verdict. Для поддержанных ролей — существующий runner:

```bash
# REVIEW_MODEL/REVIEW_EFFORT — реально доступные и разрешённые значения владельца.
: "${REVIEW_MODEL:?Choose an available approved reviewer model}"
: "${REVIEW_EFFORT:?Choose supported reasoning effort}"
.venv/bin/python tools/run_codex_role.py run \
  --profile native --root . --task D08-delivery --role program_design_review \
  --request .playbook-artifacts/delivery-review-request.md \
  --model "$REVIEW_MODEL" --reasoning-effort "$REVIEW_EFFORT" \
  --timeout-seconds 900
```

Исполнитель создаёт указанный request из актуальных фактов; не запускать пример с
несуществующим файлом. Для implementation используйте `slice_review`, для
maintainability — соответствующую роль. Не обязательно запускать все роли всегда.
Native-профиль здесь используется для аудита репозитория, не отменяет Governed
approval в downstream. Другие роли выполняются по `docs/codex_exec_subagent_protocol.md`.

Сохранённый результат повторно проверить `run_codex_role.py verify --root . --result
<actual-result.json>`. Использовать фактический путь из runner, не выдумывать имя.
Оценить status, verdict и findings раздельно. Исправляет основной implementer,
а не read-only reviewer. После изменений affected checks и review повторяются.
Недоступный процесс/модель — незавершённая проверка, не основание для PASS.

Сторонний агент допустим при разрешённой передаче данных и доступном инструментарии.
Зафиксировать новую сессию, read-only, модель, версии, actual scope и ограничения.
Не фабриковать Role Runner evidence для другого провайдера. При capacity/denial
не копировать авторизацию и не отключать sandbox. Смену провайдера согласовать,
если она меняет разрешённую передачу данных.

## E. Честное сравнение с обычным агентом

Используйте `evals/native/harness/README.md` и текущий `harness_adapter.py`.
До расхода токенов прогон fake CLI/compare подтверждает совместимость команды.
Одна и та же основная модель, задача, база, tools, права и бюджет для plain и
Playbook; меняется исследуемый пакет/процесс. Обычному агенту не запрещать
штатную проверку ради преимущества. Полный Playbook включает reviewer/fix;
запрет вложенного reviewer означает отдельный instruction-only опыт.

Существующие booking/contacts — диагностика, не покрытие всей таблицы C.
Расширять набор свежими представительными историями по реальным пробелам.
Считать main+review+fix+eval+время человека, неизвестное оставлять unknown.
Один trial не подтверждает стабильность; лимиты/повторы/порядок определить до
опыта. Таймаут остаётся таймаутом, даже если промежуточный код проходит scorer.
Сохранить отрицательные исходы. Fingerprints и frozen результаты не исправлять.

## F. Итог и реальные люди

В итоговом отчёте каждой capability сопоставить версию, сценарий, техническое
свидетельство, model/browser evidence, пользовательское наблюдение и пробел.
Отдельно `source-ready`, `technical-ready`, `live-workflow-checked`,
`field-observed`, `release-approved`. Отсутствие одного не маскируется другим.
Показывать open P0/P1 и решения по P2/P3, расходы, неизвестные счётчики и
актуальные команды. Итоговый независимый review — после исправлений.

Пилоты из `product/pilots/` выполняются с настоящими людьми и разрешёнными данными.
Преподаватель сам инициирует последующее изменение в новой сессии. Помощь автора
считать отдельно. Использование через неделю/месяц не симулировать в одном запуске.
Распространение/права/платежи — решение владельца после результатов, не побочный
эффект git merge. Готовый ZIP не означает готовый пользовательский продукт.

## Источники интерфейса запуска

Официальная документация OpenAI проверена 20.09.2026:
https://developers.openai.com/codex/noninteractive — `exec`, `--json`, `--ephemeral`,
read-only/explicit sandbox и запись итогового сообщения. Реальный CLI сверить
через `codex --version` и `codex exec --help` в своей среде. Команды Playbook
выше основаны на существующем `tools/run_codex_role.py`, не на догадке об API.
