# Preview.3: упаковка, подключение и первый результат

> Исторический отчёт. Подробные материалы сохранены в [неизменяемом архиве](../README.md); ссылки ниже ведут на проверенный коммит.

Дата: 2026-09-19. База изменений: `4eb96cce5623bd397b47e837a6aea286b0695963`.
Работа выполнена в ветке `docs/codex-frontend-skills-mcp-20260919`.
Master `d570163ab17ec3b4245187c778f1e8d89af9690f` и downstream не изменялись.
Это диагностическая проверка кандидата, не публичный релиз или исследование новичков.

## Получившийся продукт

Первый путь: **распаковать → открыть START.html → выбрать «Мой проект» в Codex →
описать задачу → открыть проверенный результат**. В папку уже включены два skills
и небольшой AGENTS block. Терминал, ручная установка скрытых файлов, выбор framework
и чтение исследовательских документов не входят в первый запуск.

Для постоянной работы с собственными проектами включён native plugin из тех же
исходников. Стартовая страница даёт запрос установки и помощь. Три независимых
измерения процесса сохранены; выбор необязателен и меняется обычными словами.

**Архив:** `Playbook-0.1.0-preview.3.zip`, 34 588 байт, 19 файлов.
SHA256: `03e6b9460943ec8d12f7e13771cdf7f7e6e4f142154d31b14f62d1d86e07431d`.
[Сборщик и инструкция](../../../distribution/native/README.md),
[идентичность артефакта](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/artifact.json), [хеши каждого файла](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/package.json).
Архив собран локально, не опубликован; исходники позволяют повторить сборку.

## На что опирались решения

| Наблюдение | Изменение | Почему |
|---|---|---|
| В прежних CLI trials `.agents` нельзя было записать из agent sandbox | Первая проба получает подготовленную папку из ZIP | Новичку не приходится решать проблему скрытых каталогов и разрешений |
| Host обнаруживает plugin skill как `playbook-native:playbook`, локальный — как `playbook` | Пользовательский запрос начинается с «Playbook» обычными словами | Не обещаем универсальный технический alias; доступен штатный picker |
| Сам по себе готовый код не объясняет новичку, как увидеть результат | Entry skill требует понятный способ открыть результат и объяснение ограничений | Проверяем результат глазами пользователя |
| Первое удаление сохранило изменённый SKILL активным, но удалило его reference | Сохраняем целую папку вне discovery и лишь затем убираем активную | Одновременно сохраняем пользовательскую работу и отключаем skill |
| Успешный install и exit 0 не гарантируют чтение skill | Отдельно считаем lifecycle, discovery и выполнение задачи | Не называем частично работающий путь готовым |

Официальные [правила packaging](https://developers.openai.com/plugins/build/plugins)
использованы вместе с локальными helpers Plugin Creator и фактическим CLI.
[Текущий quickstart OpenAI](https://learn.chatgpt.com/docs/quickstart?setup=app)
подтверждает выбор Codex в desktop; [проектная документация](https://learn.chatgpt.com/docs/projects)
объясняет основную папку для discovery. Это источник инструкции, не доказательство
пройденного desktop walkthrough. Источники прочитаны 19.09.2026.

## Что действительно выполнено

| Проверка | Наблюдаемый результат | Доказательство / граница |
|---|---|---|
| ZIP | 5 тестов: повторяемость, хеши, извлечение с кириллицей/пробелами, сохранность существующих архивов/checksum, запрет symlink | [test_build.py](../../../distribution/native/test_build.py); Linux, не Windows/macOS |
| START.html из финального ZIP | 48 сочетаний; пустой ввод, карточки, буквальный пользовательский текст, copy/fallback, помощь, 390/1280 px; нет page errors/внешних requests | [launcher-check.json](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/launcher-check.json); clipboard API stub, реальная selection fallback; не OS clipboard |
| Repo-local discovery | Из распакованной папки без `.git` host обнаружил оба enabled skills | [starter-discovery.json](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/starter-discovery.json); свежий container, app-server |
| Native plugin lifecycle | Install, reinstall без изменения cache bytes, update с cachebuster, remove; новые app-server sessions; пользовательские файлы не изменены | [lifecycle.json](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/lifecycle.json), offline Linux container; не модель и не desktop UI |
| Connect/reconnect | Правильный root override, один блок, 6 точных файлов; повтор без изменений bytes/mtime/mode | [до](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/connection-before.json), [после](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/connection-after.json); независимый агент, затем продолжение той же сессии |
| Update | Меняется только frontend SKILL; совместимые исходное обновление и пользовательская строка сохранены | [наблюдения агента](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/connection-observations.md); проверка файлов, не fresh-session discovery |
| Первое remove | **FAIL:** custom skill остаётся активным, reference потеряна | [наблюдения](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/connection-observations.md), [независимая проверка](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/removal-verification.json); не скрыто успешным retry |
| Removal regression | Полная резервная папка вне discovery, нет активного SKILL/блока; остальные bytes сохранены | [до](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/remove-before.json), [после](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/remove-after.json); follow-up в новой fixture после узкой правки инструкции |
| Новая frontend-задача | Агент создал сайт, открыл Chromium, прошёл форму/ошибки/клавиатуру, просмотрел 8 изображений, исправил проблемы, перепроверил | [его checks](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/agent-browser-checks.json), [полученный сайт](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/demo-output/index.html); полный цикл в доступной среде |
| Проверка результата другим проходом | Родитель самостоятельно проверил выбор занятия, пустую/невалидную форму, успех/reset, ширины 360/390/768/1440, file://; ошибок/внешних запросов не наблюдал | [independent-ui.json](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/independent-ui.json); это дополнение, не подмена проверки исполнителя |
| Смена режима | «Теперь сначала только план» после создания: понятный план расписания; все 60 файлов, включая локальные служебные файлы, совпали по хешам | [plan-switch.json](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/plan-switch.json), [ответ](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/plan-switch-final.md) |
| Clean-container model trial | **BLOCKED:** агент заявил выбор Playbook, но не смог прочитать инструкции; в финале это сообщил; файл проекта не изменился | [final](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/native-discovery/final.txt), [events](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/native-discovery/events.jsonl), [summary](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/native-discovery/summary.json); exit 0 не засчитан как skill execution |

Native lifecycle использует CLI 0.155.1, Python 3.12 container и official helpers;
контейнер удаляется после проверки, сетевой доступ отключён. Глобальные каталоги
меняются только внутри disposable container. Host config, модель и разрешения
не изменялись. Контейнерная проверка модели использовала тот же `gpt-6-astra/xhigh`,
штатную авторизацию CLI и read-only sandbox, approval never; credentials в evidence
не копировались. [Версии и хеши исходников](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/environment.json).

Первая версия lifecycle probe ошибочно ожидала unprefixed names и упала:
[сохранённая ошибка harness](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/lifecycle-first-attempt.json). Исправлена
проверка фактических names, а не пакет ради прохождения неверного ожидания.
Первый model trial не включал companion executable `codex-code-mode-host`:
[исходная ошибка](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/native-discovery-missing-host/events.jsonl). После
добавления штатного executable ошибка запуска исчезла, но чтение skill всё ещё
не подтверждено. Повторный результат также сохранён как blocked; разрешения
не расширялись, дальнейшие одинаковые model retries не запускались.

## Условия агентских испытаний

Два независимых collaboration-agent входа с минимальным контекстом: новый сайт и
подключение к synthetic backend. Последующие update/remove/смена режима —
продолжения, а не новые независимые участники. Это forward-testing по Skill Creator,
а не дополнительные роли для каждой пользовательской задачи.

Для UI fixture заранее подготовлены локальные skills, block и README с указанием
уже установленного Playwright/Chromium. Это помощь среды: новичок сам инструменты
не настраивал, desktop onboarding этим не доказан. Агент использовал законно
доступные инструменты текущего host; ранее отклонённые CLI/MCP действия не обходились.
Трасса collaboration-agent не экспортирована как CLI JSONL; его наблюдения,
проверяемые артефакты и независимый browser probe перечислены раздельно.

Запрос первого задания совпадает с учебной карточкой: сайт преподавателя английского,
услуги/цены/форма, вымышленные тексты, локальная проба без оплаты и реальной отправки,
телефон, проверка формы, простой способ открыть. Агент исправил найденные проблемы
разметки списка и мобильных заголовков. Выходной сайт — **результат испытания**, не
заранее подготовленный ответ внутри распространяемого архива.

Родитель просмотрел desktop и mobile screenshots результата, а также финальную
стартовую страницу. [Старт desktop](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/images/start-desktop.png),
[старт mobile](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/images/start-mobile.png), [пример результата](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/images/demo-desktop.png),
[форма на телефоне](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/images/demo-mobile-success.png). Исходный browser script сохранён в `demo-output/tests/browser-check.cjs`;
он использует Playwright по пути испытанной среды, указанному в README результата.
Это зафиксированный evaluator, не универсальная установка зависимостей.
Субъективное качество дизайна
не превращено в автоматический балл; полного accessibility audit, Safari/Firefox
и usability с человеком не было. Стоимость collaboration trials не экспортирована.

## Проверки самого репозитория

- Plugin Creator validator и Skill Creator validators обоих skills — PASS.
- Archive tests — 5 PASS; существующие runner tests — 5 PASS.
- Полный pytest: **222 passed, 12 skipped, 2 failed** за 92.76 s.
  Это те же исторические ошибки frozen asset manifest и несовпадения установленного
  Codex с frozen toolchain, ранее воспроизведённые на исходном `d070f4e`.
  [Сводка](https://github.com/ashishki/AI_workflow_playbook/blob/b80eb56aebef97615724995dacc6b6512edbd15b/reports/native/2026-09-19-onboarding/evidence/repository-checks.txt). Исторические хеши не переписаны.
- Integrity check — PASS с двумя прежними предупреждениями о generated cognition.
- Проверка ссылок изменённых документов, синтаксиса новых инструментов и
  `git diff --check` — см. итоговую запись в [handoff](../../../docs/handoffs/CODEX_FRONTEND_SKILLS_MCP_HANDOFF.md).

Первые [12 CLI trials](../2026-09-19/REPORT_RU.md) остаются отдельным историческим
отчётом. Новые результаты не превращают их blocked browser в успешный запуск.
Нет доказанного ускорения или превосходства над обычным Codex.

## Следующий продуктовый шаг

Пакет технически подготовлен для управляемой пробы. Нужны desktop walkthrough на
заявленной системе и [пилот с 3–5 новичками](../../../docs/native/PILOT_RU.md).
Остаются другие frameworks, monorepo, negative setup collisions и stale/wrong
preview trials; это backlog проверки границ, а не обязательные этапы для пользователя.

От владельца требуется решение о правах использования распространяемого пакета;
[LEGAL_STATUS](../../../docs/LEGAL_STATUS.md) не изменён. После desktop smoke и
пилота — решение о выпуске. Никому не писали, публичный каталог/релиз не создавали.
