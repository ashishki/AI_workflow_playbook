# План внедрения Codex frontend pack и оценки skills/MCP

Статус: **PROPOSED — не исполнять как утверждённый task graph**. Дата: 2026-09-19.
База исследования: `d570163ab17ec3b4245187c778f1e8d89af9690f`.

Основания, источники и ограничения: [исследование](CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md).
Запуск следующей сессии: [handoff](../handoffs/CODEX_FRONTEND_SKILLS_MCP_HANDOFF.md).

Этот план описывает будущие изменения, а не результаты их реализации. CF-ID ниже — идентификаторы предложения, не уже зарегистрированные задачи `docs/tasks.md`. После согласования нужно сопоставить их с реальным task/feature/slice registry. Существующие контракты и human approval имеют приоритет.

## 1. Цель, границы и проверяемый результат

Сделать frontend-разработку в Codex воспроизводимой: агент понимает продукт, использует подходящие skills, проверяет правильную сборку и передаёт человеку достоверные доказательства. Не превращать Playbook в frontend-framework, runtime или обязательный MCP-host.

Исходный вариант: текущий Codex + действующий Playbook + уже доступные инструменты проекта. Первый кандидат добавляет только scoped frontend skills и их проверяемую интеграцию. Browser MCP — отдельный условный эксперимент. Нулевое число MCP остаётся допустимым результатом.

Продуктовые изменения выполняются в выбранном downstream-репозитории, а не в Playbook. Шаблоны, валидаторы и методика — в Playbook. Не добавлять React/Next.js, Figma, browser runtime или внешнюю базу памяти в core requirements для всех пользователей.

## 2. Кто что делает

| Участник | Ответственность | Ограничение полномочий |
|---|---|---|
| Владелец продукта — Артём | Выбор задачи и метрики, согласование design и полномочий, решение по пилоту, merge/release | Не подменять его согласие текстом модели или успешным exit code |
| Основная сессия Codex | Инвентаризация, подготовка дизайна, управление задачами, сбор актуального состояния и предъявление результата | Следовать выбранной delivery-модели; не создавать вторую очередь и не самоподписывать approvals |
| Codex implementer | Scoped код, тесты, исправления, реальные команды, evidence и handoff | Не выполнять независимое ревью собственного результата; не менять критерии для получения PASS |
| QA-driver | Запуск приложения/браузера, фикстуры, e2e, скриншоты, trace и console evidence | Это исполнитель с ограниченными побочными эффектами, а не read-only reviewer; без production-данных и деплоя |
| Независимый Codex reviewer | Проверка дизайна либо diff/evidence в свежем контексте | Использовать существующие поддерживаемые роли и sandbox; не исправлять код и не принимать baseline за человека |
| Целевой пользователь | Выполнение продуктовой задачи без подсказок автора реализации | Наблюдение пользователя не заменяет security и regression checks |
| CI/детерминированные инструменты | Контрактные проверки, актуальность evidence, тесты и машинные stop conditions | Не принимают продуктовые компромиссы и не выдают человеческое разрешение на merge |

В поддерживаемом Role Runner использовать `product_design_review`, `program_design_review`, `slice_review`, `maintainability_review`. Frontend/UX checklist — область существующей роли, а не выдуманный новый CLI role. Для дополнительных Test Critic/security сессий использовать только явно поддерживаемый текущей политикой механизм. Отсутствие независимого запуска записать как NOT_RUN, не заменять саморевью.

Основной Codex сохраняет фактические настройки пользователя. Reviewer использует профиль из текущей `REVIEW_POLICY`; имя модели и effort записываются в evidence. Не понижать режим молча. Codex Direct implementer не запускает вложенный Codex: независимые reviewers запускаются только через разрешённый orchestration/harness path.

## 3. Последовательность CF-00–CF-09

Общая цепочка: `CF-00 → CF-01 → CF-02 → CF-03 → CF-04 → CF-05 → CF-06 → CF-08 → CF-09`.
`CF-07` — условная ветка после CF-05, её результаты включаются в CF-08. Если MCP не нужен, CF-07 закрывается решением «не применять», не пустым PASS. Этапы можно разбить на меньшие утверждённые слайсы; не запускать пишущие агенты параллельно над общими файлами/средой.

### CF-00. Инвентаризация, baseline и утверждение объёма

**Ответственный:** основная сессия Codex; принимает Артём. Зависимостей нет.

Проверить HEAD/branch/dirty state, `docs/tasks.md`, session state, current design/reviews, выбранную delivery-модель, доступные Codex/browser-инструменты. В downstream-репозитории установить framework, lockfile/version, команды запуска и тестов, наличие дизайн-системы, целевые поверхности и пользователей. Не считать Telegram-бот веб-приложением и не приписывать проекту React без проверки.

Выбрать одну обратимую frontend-задачу: например, небольшой существующий экран со сценарием успеха, пустого результата, ошибки и повторного действия. Примеры не являются выбором конкретного продукта за пользователя. Для Mini App включить проверку целевого WebView; для чистого бота заменить visual matrix диалоговыми сценариями.

**Результат:** текущий inventory, зафиксированный baseline, Feature Design с AC, scope, бюджетом, риском, visual route, схемой evidence и rollback. Использовать существующие `docs/design`, task registry и review/approval tools, а не параллельные файлы решений.

**Проверка:** команды baseline действительно запущены; неизвестное отмечено неизвестным; AC наблюдаемы; dependencies и версии установлены из репозитория. Отрицательный сценарий: неутверждённый или изменённый design не допускает start.

**Gate:** обязательные design reviews и человеческое approval по текущему workflow. До gate допустимы только исследование и подготовка дизайна. **Rollback:** отказаться от proposal без установки пакетов.

### CF-01. Видимость и доверие к реально загружаемым skills

**Ответственный:** implementer; проверка независимым reviewer с security lens. Depends: CF-00.

Изменяемые поверхности: `tools/skill_security_gate.py`, соответствующие unit/integration tests, security policy и installer — только если нужен для утверждённого решения. Добавить `.agents/skills` и явную модель effective roots; сохранить проверенные legacy roots. Учесть repo/nested scopes, разрешённые symlinks и дубликаты. Не читать глобальные/private папки без разрешения; обозначать непроверенные scope как incomplete coverage.

Trust record фиксирует источник, версию/хеш, лицензию, install scope, обновления, capabilities, scanner evidence и triage. Если skill загружает другие instructions из изменяемой ссылки, зафиксировать также их версию или явно признать невоспроизводимость. Локальные first-party и внешние skills не объявлять одинаково безопасными по имени: определить provenance и проверяемую политику для каждого.

**Тесты:** `.agents` fixture обнаружен; внешний skill без trust record не проходит; legacy найден; duplicates не удваиваются; неизвестный root не скрывается; разрешённый symlink проверен; выход symlink за разрешённую область отклонён/эскалирован; изменение pinned инструкции обнаружено. Отсутствие любых skills остаётся корректным no-op, но только при известном охвате.

**Gate:** позитивные и отрицательные тесты, независимое ревью, отсутствие регрессии текущих generated modes. **Rollback:** выключить новый pack и вернуть изменения отдельным revert, сохранив отчёт о причине. Нельзя «откатить» проблему, снова объявив непроверенный каталог безопасным.

### CF-02. Обязательные ограничения в bounded context

**Ответственный:** implementer; независимое slice/maintainability review. Depends: CF-01.

Поверхности: `tools/render_slice_context.py`, при необходимости `schemas/instruction_manifest.schema.json`, renderer tests. Сохранить небольшой пакет, но выбирать обязательные excerpts по утверждённым идентификаторам/разделам, а не только первым N символам. Записывать hashes и omitted optional material. Required missing/stale fragment должен останавливать подготовку пригодного пакета.

**Тесты:** обязательное правило после 6 000 символов включается либо сборка блокируется; потерянная ссылка не пропускается молча; изменившийся источник помечает пакет устаревшим; слишком большой required fragment не обрезается без решения; обычный короткий packet остаётся компактным. Проверить совместимость существующего manifest или явную версионированную миграцию.

**Gate:** coverage всех обязательных правил и отрицательные тесты; reviewer видит source-to-packet mapping. **Rollback:** отключить новый renderer с явным безопасным чтением полных обязательных источников; не использовать урезанный пакет как полный контракт.

### CF-03. Правильная сборка и пригодное browser evidence

**Ответственный:** implementer + QA-driver; reviewer проверяет, человек утверждает контракт. Depends: CF-02.

Поверхности: `docs/testing/ui_verification.md`, runtime verification contract, существующие receipt/project verification consumers и project-owned browser helper. Для новых данных выбрать companion artifact либо версионированную схему и миграцию. Нельзя просто дописать произвольные поля в схемы с `additionalProperties: false`.

Связать task/slice, commit, dirty tree fingerprint, worktree root, фактически наблюдаемую build identity, target URL/environment, fixture и browser versions, состояние/viewport, команды и hashes артефактов. URL и PID сами по себе не подтверждают версию кода. При необходимости использовать тестовый build marker; не публиковать секреты или внутренний путь через production endpoint.

Сначала project checks; затем запускается именно проверяемая сборка, проверяется identity; после — сценарии, screenshots/diffs и console/trace. Отдельные worktrees должны иметь раздельные порты, browser profiles и тестовые данные либо явную блокировку общего ресурса.

**Тесты:** неправильная сборка на правильном порту; устаревший screenshot; изменение кода при том же commit; пропущенный сценарий; отсутствующий artifact; подменённый hash; занятой порт; неготовый сервер. Всё это не должно приводить к принятому evidence. Позитивный тест доказывает правильную связку.

**Gate:** валидный сценарий проходит, каждый critical negative case отклоняется; baseline policy не ослаблена. **Rollback:** отключить adapter, оставить явно ручную проверку со статусом ограничения; не выдавать отсутствие evidence за PASS.

### CF-04. Маленький opt-in frontend pack

**Ответственный:** implementer; reviewer проверяет triggers/authority/совместимость. Depends: CF-03.

Добавить только утверждённые шаблоны `playbook-frontend-design`, `playbook-frontend-verify`, `playbook-frontend-review`. Имена предложены, пути шаблонов и installer flag выбираются в design. Установить в downstream `.agents/skills` только после CF-01. Skills вызывают существующие tools; не копируют весь Playbook и не создают альтернативные approval/review loops.

React/performance/composition references подключать только к подходящему стеку и задаче. Для каждого внешнего источника проверить лицензию и полный dependency chain; не ставить целые marketplaces, Superpowers или десятки plugins. Исходный код внешнего skill не копировать без установленного основания для переиспользования.

**Тесты:** явный вызов обнаруживается installed Codex; нужная задача загружает нужные references; backend-задача не тянет frontend pack; не хватает browser capability — BLOCKED для обязательной проверки; install не затирает пользовательский config; uninstall оставляет исходные настройки; skill не может сам принять baseline/design. Разделить contract fixtures и реальные Codex invocation trials.

**Gate:** реальные smoke trials плюс deterministic contracts; отсутствие установленного Codex означает NOT_RUN и блокирует заявление о runtime-совместимости. **Rollback:** удалить/отключить только созданные pack files, восстановить config по recorded diff.

### CF-05. Полный Codex-only frontend-слайс без MCP

**Ответственный:** implementer и QA-driver; reviewer отдельно; человек принимает. Depends: CF-04.

Выполнить выбранную в CF-00 задачу в downstream feature branch: UX/design direction → AC/tests → код → проектные проверки → browser behavior → stable screenshots → bounded fixes → независимый review → пользовательская проверка. Использовать существующий стек, компоненты и model settings. Для исследования можно CLI; регрессии сохраняются как обычные tests и не требуют свободного рассуждения модели при каждом запуске.

**Evidence:** AC-to-test map, build identity, state/viewport matrix, console/network disposition, visual baseline/current/diff, a11y observations, реальные команды, findings и human decision. Loading, empty, error, retry, long content и permission states включать по смыслу задачи, а не формально все подряд.

**Gate:** все required AC подтверждены; свежесть evidence проверена; нет нерешённых stop-ship; каждый новый/изменённый обязательный visual baseline принят человеком. Ошибки layout нельзя скрывать mask/повышением threshold. **Rollback:** revert слайса, восстановление исходного baseline, сохранение причины и evidence.

### CF-06. Понятный status/resume и ограниченный learning loop

**Ответственный:** implementer; independent maintainability review; человек проверяет восстановление. Depends: CF-05.

Расширить существующие `feature_workflow status/next/context/check`, а не строить dashboard/backend. Показать текущий slice, evidence freshness, точный blocker, владельца следующего действия и безопасный шаг. Checkpoints адресовать по repo/run; общий временный файл не должен перезаписывать другую сессию.

В существующем decision log хранить отвергнутые варианты, rationale и условия пересмотра. Повторяемый инцидент становится кандидатом на тест/guard через обычный review, не автоматически переписывает contract. Для существенных ограничений показать claimed vs effective coverage; prompt-only правило не маркируется runtime enforcement.

**Тесты:** новая сессия восстанавливает правильную задачу; stale approval/evidence заметны; две сессии не смешиваются; отсутствующий hook не считается активным; разрешённое действие проходит, запрещённое отклоняется поддерживаемым механизмом; неизвестный tool event не интерпретируется как проверенный.

**Gate:** человек может определить следующий шаг из вывода без ручного чтения архивов; измерить время и вмешательства, не объявлять заранее выигрыш. **Rollback:** старый status остаётся доступен; новая проекция не является authority.

### CF-07. Условный MCP-пилот

**Ответственный:** основная сессия готовит решение; человек разрешает scope; implementer/QA запускает; независимый reviewer проверяет. Depends: CF-05, а status из CF-06 желателен.

Назвать нерешённую CLI-путём потребность. Выбрать **один** browser interface: Playwright MCP для взаимодействия или Chrome DevTools MCP для требуемой диагностики. Figma подключать отдельным этапом только для реального макета. Не менять модель, skill semantics и browser transport в одном сравнении.

Проверить effective Codex configuration, server/package identity, dependencies, allowlist tools/resources, auth, scopes, timeouts, data flows, telemetry и version drift. Sandbox файлов Codex не гарантирует ограничение сетевых/удалённых побочных эффектов MCP. Browser interaction способен отправить форму и изменить backend даже через «read-oriented» сервер: тестовый аккаунт, синтетические данные и изоляция обязательны.

Figma стартует с конкретных frames и read-tools. Запись на canvas, deploy, production writes и широкие grants вне scope. Remote server может обновляться без pin; сохранить tool schemas/metadata и переоценивать drift. Не коммитить tokens/config secrets; не подключать личный авторизованный browser profile.

**Тесты:** allowed read; denied side effect; неверный ресурс; timeout/offline/expired auth; schema drift; отсутствие обязательного tool; очистка сессии и отзыв credentials. Запрещённые действия проверять безопасной фикстурой, не реальным production запросом.

**Gate:** permission tests и matched comparison показывают достаточное основание для ограниченного применения. **Rollback:** отключить server, отозвать доступ, очистить profile и вернуться к CLI; не ломать Playwright Test regression suite. Допустимо завершить без установки MCP.

### CF-08. Парное сравнение качества, времени и стоимости

**Ответственный:** evaluation driver запускает; независимый reviewer оценивает evidence; человек adjudicates и решает. Depends: CF-05, CF-06; CF-07 только при наличии MCP-кандидата.

Использовать существующий `companion/ai_workflow_harness_lab` и его evidence/cost conventions; при необходимости добавить project-specific suite и adapter отдельным утверждённым слайсом. Не писать второй eval framework. Точный протокол — раздел 4 ниже.

**Gate:** воспроизводимые matched runs и проверяемые артефакты; все исключения объяснены; отрицательный результат не скрыт. Реальные показатели не заполнять синтетическими числами. **Rollback:** прекратить эксперимент по бюджету; сохранить частичный результат как inconclusive, не превращать в маркетинговый вывод.

### CF-09. Решение, opt-in rollout и передача

**Ответственный:** Артём принимает; Codex готовит evidence summary и изменения docs. Depends: CF-08.

Выбрать `adopt`, `adopt_limited`, `inconclusive` или `reject` для каждого независимого компонента. Это решения пилота, не новые статусы текущих validators. Skills можно принять, MCP отклонить; полезный identity check не требует принять весь pack.

Обновить канонические документы/ADRs только после approval. Зафиксировать поддерживаемые версии, права, install/uninstall, известные ограничения и стоимость сопровождения. Начать с одного продукта, расширять после повторного подтверждения. Сохранить текущие default settings для остальных проектов.

**Gate:** полный handoff, актуальные receipts/reviews, owner approval и отдельное человеческое merge/release. **Rollback:** отключение opt-in pack, revert конкретных изменений, восстановление prior config/baselines и сохранение evidence.

## 4. Протокол оценки: что сравниваем и в каком порядке

### 4.1. Не смешивать четыре вмешательства

| Вариант | Конфигурация | Что позволяет оценить |
|---|---|---|
| A | Текущий Codex + Playbook + одинаковые доступные project/browser tools | Реальный baseline, не искусственно беспомощный агент |
| B | A + утверждённые frontend skills | Добавочную пользу инструкций/упаковки |
| C | B, но browser interface заменён CLI → выбранный MCP | Пользу/стоимость интерфейса инструментов при сопоставимых возможностях |
| D | Отдельная Figma-задача с одинаковым design reference, экспорт против MCP-read | Получение design context, не качество другой модели или другого макета |

Общие safety/identity исправления CF-01–CF-03 применить одинаково к A и B до сравнения skills; их собственную пользу проверить отдельными negative fixtures. Исходный снимок workflow сохранить как historical baseline. Не приписывать skill эффект от одновременно исправленного test runner.

### 4.2. Набор и контроль переменных

Предлагаемый начальный бюджет — четыре класса реальных задач по три matched повтора: 12 пар/24 запуска для A/B. Это предложение к approval, не выполненный эксперимент и не расчёт статистической мощности. Повторы одной задачи не являются 12 независимыми продуктами. При меньшем бюджете сообщать ограниченную уверенность.

Классы: небольшой UI fix; форма со state/error handling; составной responsive screen; regression/debugging задача. Для текущего продукта подобрать реальные аналоги, не генерировать удобный benchmark. Выделить development cases для настройки и отдельные holdout cases; не подгонять skill по holdout ответам.

Зафиксировать одинаковые model/effort, repo base, acceptance criteria, permissions, budgets, framework/browser/fonts, fixtures, locale/timezone, viewport, tool versions и возможности. Случайно/сбалансированно менять порядок A/B. Каждый запуск начинается с clean isolated workspace; не переносить готовый patch между вариантами. Регистрировать все retries, early stops, manual hints и фоновую нагрузку. Секреты и частные данные не должны попадать в dataset.

### 4.3. Порядок проверки каждого результата

1. Сначала identity, integrity, scope и permissions. Невалидный запуск не становится quality PASS.
2. Затем typecheck/lint/unit/component и поведенческие e2e; проверить все обязательные AC.
3. Затем stable screenshots/diff и console evidence. Новый baseline — кандидат для человека, а не автоматический эталон.
4. Затем a11y и выбранные performance budgets. Автоскан дополняется keyboard/focus/zoom проверками; измерения повторяются в одной среде.
5. Затем независимый review и наблюдение целевого пользователя; где возможно скрыть название варианта от оценивающего.
6. Наконец время, токены, стоимость и операторские затраты — только вместе с качеством, не вместо него.

### 4.4. Метрики, stop conditions и вывод

| Показатель | Как измерять | Правило |
|---|---|---|
| Доля принятых задач | Accepted tasks / все начатые admissible tasks; invalid runs отдельно | Не исключать неудобные failures после просмотра результата |
| Полнота required evidence | Подтверждённые required AC / все required AC | Для приёмки задачи 100%; отсутствие evidence блокирует, не обнуляет знаменатель |
| False completion, scope/permission violations, stale evidence acceptance | Случаи с конкретной воспроизводимой ссылкой | Любой наблюдённый critical случай останавливает rollout; ноль в пилоте не доказывает нулевой риск вообще |
| Реальное удобство | Успешность целевого сценария без подсказок, ошибки и необходимость помощи | Человек фиксирует наблюдение; модель не придумывает отзыв |
| Визуальная корректность | Состояния/viewport, diff disposition и человек | Нет универсального pixel threshold или «9/10»; пороги и rationale задаются до пилота |
| Операторские затраты | Активные минуты, число hints, approvals, восстановлений контекста | Считать и setup/maintenance overhead, а не только генерацию |
| End-to-end время и стоимость | От начала до принятия, retries/tools/reviews; фиксированный источник цен | Unknown cost остаётся unknown; токены не равны деньгам |
| Устойчивость | Повторяемость исхода, flake rate, восстановление после interruption | Уточнять причины environment failures и повторы |

Не выбирать произвольное «ускорение на 20%» после просмотра результатов. В CF-00 человек задаёт practically meaningful benefit и допустимые trade-offs для этого продукта; guardrails качества не компенсируются скоростью. Сообщать paired differences и разброс, а не только среднее. Маленький пилот даёт bounded operational decision, не общую доказанную эффективность.

## 5. Проверки изменений самого Playbook

В полноценном checkout с необходимыми зависимостями должны выполняться существующие команды:

```bash
python -m pytest -q
python tools/verify_playbook.py --root .
python tools/integrity_check.py --root .
```

Дополнительно — targeted tests изменённых tools и generated-project matrix. Пути новых тестов определяются реализацией; вымышленные имена не считать существующими. CI проверять по точному HEAD, отдельно от локальных запусков. После изменения evidence-sensitive кода пересоздать актуальные артефакты и ревью по действующей политике.

## 6. Передача между сессиями

Каждый закрытый слайс оставляет branch/HEAD, scope и diff, реально выполненные команды с результатом, current design approval, evidence/review references, открытые findings, остаток бюджета и следующее допустимое действие. В source-of-truth файлах фиксируется статус; handoff лишь направляет к нему.

Новый агент не перезапускает закрытые задачи, не повышает authority research-документа, не трогает `master` напрямую и не заявляет успешный тест без запуска. Доступ к браузеру, configured MCP и установленный skill проверяются заново в конкретной среде. Решение «MCP не нужен» считается нормальным результатом исследования.
