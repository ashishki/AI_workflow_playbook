# Playbook Native: план доведения до выпуска

Статус: **preview.5: автоматический Role Runner, четыре сценария Harness Lab, CI на Windows/macOS/Linux; desktop usability ещё не подтверждён**. 2026-09-19.
Этот план заменяет CF-00–CF-09. Это backlog работ, а не новый пользовательский
workflow: подписчик не выполняет эти этапы для каждой задачи.
Текущий цикл улучшений — [короткий протокол](../native/DEVELOPMENT_RU.md);
используем существующий Harness Lab, Ground Truth Lab отложен.

[Модель продукта](CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md) →
[исходный пакет](../../plugins/playbook-native/README.md) →
[быстрый старт](../native/QUICKSTART_RU.md).

## 1. Граница готовности

В этой ветке есть два `SKILL.md`, project block, browser reference и plugin
manifest. Добавлены [единый старт](../native/start.html), три независимых измерения
процесса и [12 диагностических запусков Codex](../../reports/native/2026-09-19/REPORT_RU.md).
Новый [onboarding-проход](../../reports/native/2026-09-19-onboarding/REPORT_RU.md)
добавил готовый архив, lifecycle и полный agent/browser пример. Это кандидат
для пилота, не проверенный массовый релиз.

| Область | Состояние кандидата | Что ещё требуется |
|---|---|---|
| Продуктовая модель | Единый вход, три измерения, простой язык, смена режима проверена | Самостоятельный проход новичков |
| Упаковка | Воспроизводимый ZIP: START.html + готовая папка + native plugin | Права и разрешение на распространение |
| Три ОС | Сборка, распаковка, контракты runtime и START/Chromium прошли CI Windows/macOS/Linux | Реальный desktop и авторизованный CLI на каждой системе |
| Независимое ревью | Включён существующий Role Runner; отдельный реальный Linux-запуск нашёл дефект | Вложенный CLI в текущем eval-host блокируется; полноценный автоматический цикл требует доступной среды |
| Native lifecycle | CLI Linux: install/reinstall/update/remove, fresh-session discovery; файлы проекта сохранены | Desktop UI, Windows/macOS |
| Repo connection | Connect/reconnect/update прошли; дефект remove исправлен и перепроверен с custom skill | Остальные негативные fixtures и monorepo |
| Frontend loop | Отдельный агент: новый сайт → Chromium → просмотр изображений → исправления → итог | Другой stack, stale/wrong-preview traps |
| Старт и режимы | 48 сочетаний, extracted ZIP, помощь, plan-only переключение без изменения файлов | Вход новичка без подсказок автора |
| Discovery | Два skills из настоящего ZIP без Git; native plugin namespaced | Полный model task после plugin install: отдельный container trial остановился на сбое tools |
| Static/repository checks | Новые targeted проверки прошли; две прежние pytest ошибки сохраняются | Не подменяют runtime/usability |
| Публичное использование | Не выпущено; черновик небольшого пилота готов | Права, desktop smoke, пилот и публикация |

Отсутствие public release, marketplace listing или лицензии не маскируется
инструкцией «просто установите». Ни один downstream пока не выбран и не изменён.

## 2. Три поставки вместо десяти стадий governance

### A. Подключение, которое можно проверить и отменить

**Выход:** один versioned Native package и краткая инструкция; цель первого
контакта — увидеть понятный setup diff и перейти к задаче без настройки процесса.

- Использовать текущие исходники `plugins/playbook-native/` как единственный
  источник skills. Выбрать один host-tested способ доставки plugin. Для CLI/IDE,
  где он недоступен, использовать те же repo-local `.agents/skills`.
- Перед публичной раздачей решить права. Native включает два файла существующего
  Role Runner; остальной набор tools/templates и исследовательские архивы в комплект не входят.
- Проверить install/connect/reconnect/update/remove в изолированных fixtures.
  Существующий `AGENTS.md`, root override, monorepo и локальные изменения должны
  переживать setup. Не менять global config или устанавливать tools без нужды.
- Проверить native discovery в новой сессии и отсутствие дубликатов skills.
  Наличие правильного `SKILL.md` само по себе этого не доказывает.
- Если agent-mediated merge регулярно ошибается, добавить маленький deterministic
  helper только для сохранения/обновления своего блока. Не писать installer
  framework до наблюдения проблемы.

Проверено: штатный lifecycle plugin на чистом Linux CLI и discovery учебной
папки из ZIP. Приоритет: пройти тот же вход через desktop на машине новичка.
Agent-mediated копирование в защищённую `.agents` не является универсальным
каналом доставки. Не лечить это отключением sandbox или новым prompts pack.

**Условие закрытия этапа:** выполнить все non-destructive сценарии таблицы ниже;
подтвердить, что повторное подключение не раздувает diff, а удаление сохраняет
проектные изменения. Текущее покрытие перечислено в отчётах. Нельзя
считать CI-проверку пакета подтверждением desktop-прохода новичка.

**Откат:** выключить plugin и убрать проектный block; локальные изменённые
skills переместить целиком вне discovery. Не удалять пользовательские notes/tests.
Этот контракт проверен на fixture после найденного дефекта удаления.

### B. Один полный цикл на реальном UI

Первый полный цикл пройден в preview.3 на новом статическом сайте; отдельная
проверка результата и смена режима тоже прошли. Нижние пункты — матрица оставшегося
покрытия; все traps и frameworks одним примером не закрыты.

**Выход:** агент исправляет наблюдаемый дефект, проверяет работающий экран,
находит и исправляет оставшуюся проблему, предъявляет краткий итог.

- Использовать маленькие изолированные fixtures внутри тестовой среды: статический
  HTML и React/Vite либо другой обычный web stack. Не брать рабочий downstream.
- Сначала один доступный браузер: native desktop либо установленный runner.
  Для headless CLI проверить путь без MCP, но не запрещать уже доступный MCP.
- Пройти сценарий формы, её error state, узкий/широкий layout и клавиатуру.
  Посмотреть screenshots, ошибки браузера при доступности diagnostics.
- Воспроизвести false-success traps: другой сервер на ожидаемом порту; старый
  screenshot после изменения кода; успешный build при сломанном submit; нет
  browser/image capability; preview другой ревизии.
- Проверить, что backend/docs-задача не грузит frontend loop, не запускает browser
  и не требует screenshots. Русские и английские задачи должны попадать в skill.
- Для большого задания проверить resume из Git + одного короткого task note.
  Не требовать загрузки всего Playbook или воспроизведения transcript.

**Приёмка:** happy path работает; trap не приводит к ложному «проверено»;
доказательства относятся к финальному состоянию; normal task не требует нового
approval; scope/permissions сохранены. Shell assertions и скриншоты приложить
к результату trial, без обязательного нового JSON-протокола.

**Откат:** disable frontend skill, сохранить проектные tests. Если native agent
уже делает эту работу не хуже, упростить skill до действительно полезной дельты
или убрать его. Сохранение написанного pack не является целью эксперимента.

### C. Выпуск для небольшого круга подписчиков

Архив и [сценарий пилота](../native/PILOT_RU.md) подготовлены. Контактов с людьми
и публикации не было. Следующая работа — наблюдать первый запуск на desktop,
а не добавлять новый слой правил.

**Выход:** конкретный install artifact, поддерживаемые environments, инструкция
на один экран, результаты пилота и понятный способ сообщить проблему.

- Провести небольшой usability-пилот с 3–5 добровольцами после разрешения на
  распространение. Вести его как product discovery, не как статистическое
  доказательство улучшения модели. Не контактировать с людьми без поручения.
- У каждого: подключение к разрешённому тестовому repo, одна понятная задача,
  итоговая проверка и удаление. Зафиксировать время, ручные подсказки, ошибки
  setup, пропущенные проверки, ненужные вопросы и непонятные термины.
- Исправить повторяемые проблемы. Не отвечать на каждую трудность новым документом
  или обязательным gate. Уменьшать текст skills, если он дублирует поведение host.
- Опубликовать пакет только после checks и отдельного разрешения на публикацию.
  В Telegram передать install link, один пример задачи и честные prerequisites.

**Предварительный критерий продолжения:** не менее 4 из 5 пользователей проходят
подключение и первую задачу без объяснения внутренней архитектуры автором;
ни одной потери пользовательских файлов, скрытой установки/расширения доступа
или ложного заявления о browser verification. Для 3 пользователей требовать
3 успешных прохода и расширить пилот перед общим выпуском.
Это продуктовый порог, заданный до испытания, не статистическая гарантия.

**Откат:** снять рекомендацию конкретной версии, оставить предыдущую проверенную
версию, дать точный remove/update путь. Не выполнять удалённую автозамену файлов.

## 3. Проверки с наблюдаемым результатом

Не создавать unit tests, которые ищут правильные слова в Markdown. Проверять
файлы до/после и реальные действия agent/host. Static validators проверяют только
структуру manifest/frontmatter/ссылок.

| Сценарий | Наблюдаемый результат | Уровень |
|---|---|---|
| Новый scratch repo | Один block, обнаруженные команды, нет выдуманных scripts | Agent trial |
| Existing AGENTS + незакоммиченная правка | Пользовательские bytes вне собственного блока сохранены | Agent trial + diff |
| AGENTS.override.md / nested app | Изменён реально читаемый scope, sibling app сохранён | Host + diff |
| Повторное подключение | Нет дубля блока или skill installation | Agent trial + diff |
| Update после пользовательской правки skill | Правка сохранена либо конкретный conflict; нет silent overwrite | Agent trial + diff |
| Remove | Удалены только собственные installation files/block | Agent trial + diff |
| Symlink target наружу / collision | Нет записи вне выбранного repo и перезаписи чужой папки | Negative fixture |
| Existing Governed project | Native не отменяет активные reviews/contracts; показывает конфликт | Agent trial |
| UI prompt RU/EN без `$skill` | Skill выбран; поведение реально проверено | Host/runtime |
| Backend/prose prompt | Нет ненужного frontend workflow | Host/runtime |
| Build pass, submit broken | Ошибка обнаружена взаимодействием, исправлена и перепроверена | Browser |
| Wrong server / stale screenshot / dirty edit | Старое evidence не предъявлено как финальное | Browser |
| Нет browser или image viewer | Code checks выполнены; UI gap явно назван | Negative environment |
| CLI/remote localhost mismatch | Нет автоматического публичного tunnel; конкретный blocker | Negative environment |
| Ошибка console / mobile overflow / focus trap | Дефект обнаружен, исправлен или явно остался в итоговом ограничении | Browser + inspection |
| Approval уже дан | Нет повторной остановки на рутинной работе | Agent trial |
| Новое внешнее действие | Локальный reviewable результат готов; запрошено только недостающее разрешение | Agent trial |

Часть runtime сценариев выполнена; точный статус и неудачи находятся в
[первом отчёте](../../reports/native/2026-09-19/REPORT_RU.md) и
[onboarding-отчёте](../../reports/native/2026-09-19-onboarding/REPORT_RU.md). Сценарий без записи в отчёте
остаётся **не выполненным**. При выполнении хранить в trial report
host/model/tool versions, fixture revision, запрос, итоговый diff, реальные checks,
полезные screenshots и ручные вмешательства. Не собирать отдельный ledger для
каждого shell command.

## 4. Как оценить пользу без лабораторной бюрократии

Baseline — современный Codex с тем же repo context, доступным браузером и хорошей
обычной постановкой задачи. Нельзя давать candidate браузер, а baseline — только
текст, и называть разницу эффектом skills.

Для первого сравнения достаточно четырёх классов задач: простой responsive bug,
форма с error state, новый небольшой экран, backend/docs negative trigger.
Использовать одинаковые стартовые snapshots, модель/effort, permissions, browser,
зависимости и критерии. Менять порядок A/B, сохранять неудачи и помощь человека.
Если поддерживается повторение, повторить пары; один красивый пример не benchmark.

| Сигнал | Как измерять |
|---|---|
| Setup friction | Время до первого рабочего запроса; interventions; необъяснённые вопросы |
| Completion quality | Сценарий выполнен; визуальные/поведенческие дефекты после handoff |
| Evidence honesty | Число неподтверждённых PASS и правильно названных gaps |
| User overhead | Сколько раз пришлось читать процесс/выбирать роль/заполнять артефакт |
| Repo footprint | Добавленные files/bytes; вне собственного блока — только полезные факты |
| Cost/latency | Фактически доступные measurements; неизвестное не превращать в ноль |

Решение: **оставить**, **сузить**, **убрать** или **недостаточно данных**. Не требовать
доказанного процента ускорения до выпуска маленького instruction pack. Требовать
работающую установку, отсутствие повреждений и false-success, приемлемый UX.
Не рекламировать улучшение качества/скорости без соответствующих данных.

## 5. Что стало с CF-00–CF-09

| Старый этап | Новое решение |
|---|---|
| CF-00: inventory/baseline/design approval | Короткий setup discovery; отдельные product decisions только при реальной неопределённости |
| CF-01: skill security discovery | Native использует discovery host; дефект старого scanner — отдельный Governed backlog |
| CF-02: bounded context renderer | Убрано из Native; AGENTS + native progressive disclosure |
| CF-03: сложная browser evidence identity | Практическая проверка своего запуска в skill; формальная provenance остаётся release-policy задачей |
| CF-04: три frontend skills | Один frontend loop + единый вход с connection reference |
| CF-05: downstream pilot | Сначала изолированные fixtures; downstream только по отдельному поручению |
| CF-06: status/learning framework | Host task/session + один repo note при необходимости; нет self-modifying policy |
| CF-07: обязательная условная стадия MCP | Нет отдельной стадии; integration только для конкретной потребности |
| CF-08: масштабный paired protocol | Небольшой честный A/B + usability пилот, без новых operational gates |
| CF-09: rollout | Versioned package, licensing, host matrix, понятный install/remove |

## 6. Совместимость и отдельный Governed backlog

Native — новый путь, не новое значение `--mode` старого initializer. Существующие
Lean-Core/Standard/Strict, schemas, receipts и Role Runner сохраняют contracts.
Уже подключённые проекты не мигрируют автоматически; формальная review policy
продолжает действовать. Native может быть выбран владельцем как замена отдельно,
после concrete diff миграции, а не как побочный эффект установки skill.

Для старого пути остаются три инженерные задачи, которые не решаются этой веткой:

- Discovery `.agents/skills` и объяснение фактического охвата external skill gate,
  включая plugin/user-scope. Добавить negative tests перед заявлением о покрытии.
- Required-context selection без молчаливого clipping/skipping в renderer.
- Observed build identity для формальных remote/release browser records.

Это maintenance существующего продукта, не блокировка обычного Native onboarding.
Не менять схемы с `additionalProperties: false` неверсированными полями.

## 7. Условия готового публичного кандидата

- Права на reuse сформулированы явно для фактически распространяемых файлов.
- Установка и удаление повторены в заявленных host/OS, новые сессии видят skills.
- Все критичные preservation/false-success сценарии проверены; нет открытого
  воспроизводимого failure, который уничтожает работу или выдаёт ложную проверку.
- Есть полный frontend trial и negative non-frontend case.
- Новичок понимает задачу и итог без чтения этого плана.
- README различает Native и Governed, source preview и публичный релиз.
- Подготовлены pinned artifact, changelog ограничений и rollback-инструкция.

Человек решает права и публикацию. Технический исполнитель может сам выполнять
подготовку, исправления и локальные проверки в разрешённой области. Ни CF-design
approval, ни новый approval для каждого пункта не требуются.
