# Приёмка Engineering Addons — 27 октября 2026

Проверенный source: `4fa266eca50ed57435f67ec61d8cef8bff890412`; общий предок
до интеграции: `2d4a3c421a788f8c4cd015960b686b2f8196c3bb`. Четыре source
skills не менялись после `dba39cffc4b417e06a310d8096d4a47fc4c4f901`.
Merge source не разрешает установку в рабочие проекты и не доказывает пользу.

## Проверки

- PASS: Linux, Python 3.12.3, 22 addon tests; `bundle.py check/doctor`, build и
  verify обеих host-раскладок, `sync_runtime.py --check`, 50 vNext tests,
  `vnext_check.py` и проверка diff. Полный suite этого checkout локально не
  запускался; исторические host locks не менялись.
- PASS: [CI исходного коммита](https://github.com/ashishki/AI_workflow_playbook/actions/runs/40563347633)
  — Linux/macOS/Windows, включая отдельные шаги vNext и whitespace.
  Предыдущий [прогон f5f2418](https://github.com/ashishki/AI_workflow_playbook/actions/runs/40562770469)
  был ложно зелёным: в Windows `vnext_check` обнаружил CRLF в двух защищённых
  файлах, но PowerShell продолжил выполнение. В `b46a82d` закреплены LF и
  отдельные шаги; в `4fa266e` whitespace проверяет фактический diff.
- PASS в ограниченных синтетических сценариях: существующий Codex CLI 0.164.0,
  ChatGPT subscription, Harness Lab command adapter, отдельный read-only fixture
  и пять свежих сессий. Каждый из четырёх явно названных skills был прочитан из
  установленного локального `.agents/skills`; обычный запрос без вызова не
  задействовал инструменты. Scorer не обнаружил изменений fixture. В разборе diff
  отмечены снятие team ACL, риск раскрытия и отсутствие тестов; уточнение спросило
  о невыясненном статусе. Browser/Heavy вызовы дали только план и честно указали
  на неисполненное. Это не полный host acceptance и не оценка пользы.
  Запрошенная модель и наблюдаемая идентичность модели неизвестны; время человека
  и полная стоимость неизвестны. Лимит — 180 с на сессию, без новой платной услуги.
- PASS локального browser fixture: Google Chrome 154.0.8037.97, localhost,
  временный профиль, синтетическая запись. Проверены пустое имя, создание,
  дубликат, отказ сохранения, reload и viewport 390×844; PNG просмотрен.
  Консоль/сетевой аудит и сравнение с agent-browser не выполнялись.
- Независимый read-only обзор первого diff выявил P1 по trust gate и P2 по CRLF;
  исправления перепроверены отдельным reviewer. Role Runner `slice_review` для
  `b46a82d` вернул validated/STOP_SHIP: gate не сверяет hash, а CI проверял
  пустой рабочий diff. Исправлены инструкция отдельной сверки с закреплённым
  source и проверка base..target. Повторный Role Runner для `4fa266e` вернул
  validated/PASS, затем `verify` — valid; без подтверждённых блокеров. Остаток:
  `bundle.py verify` не связывает checkout с trust record автоматически, эту
  связь должен установить принимающий проект. Manual dispatch CI проверяет
  последний commit, а не весь много-коммитный диапазон.

## NOT_RUN / BLOCKED и решения

Claude Code отсутствует — все его host-сценарии NOT_RUN. `agent-browser` и `heavy`
отсутствуют: их реальные прогоны и сравнения BLOCKED, установка не выполнялась.
Три чередующихся baseline/candidate повтора, полная стоимость, fresh-session
continuity на реальном проекте и польза всех четырёх дополнений — NOT_RUN.
SkillSpector scan и downstream trust approval не выполнялись. Все четыре дополнения
для обоих hosts остаются **KEEP_EXPERIMENTAL**; сценарии и ограничения по каждому
зафиксированы в [results.json](results.json).

Сырые synthetic traces, отчёты Role Runner и просмотренный PNG оставлены только
в локальном `.playbook-artifacts/`; этот игнорируемый каталог может отсутствовать
в другой копии. Ни один другой проект не изменялся. Модельные сообщения, фиктивный
browser fixture и успешная проверка упаковки не являются production evidence.
