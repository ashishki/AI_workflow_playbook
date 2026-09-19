# Playbook Native: план доведения до выпуска

Статус: **продуктовый кандидат и исходный preview-пакет**. 2026-09-19.
Этот план заменяет CF-00–CF-09. Это backlog работ, а не новый пользовательский
workflow: подписчик не выполняет эти этапы для каждой задачи.

[Модель продукта](CODEX_FRONTEND_SKILLS_MCP_ADOPTION_RU.md) →
[исходный пакет](../../plugins/playbook-native/README.md) →
[быстрый старт](../native/QUICKSTART_RU.md).

## 1. Граница готовности

В этой ветке есть два `SKILL.md`, project block, browser reference и plugin
manifest. Добавлены [единый старт](../native/start.html), три независимых измерения
процесса и [12 диагностических запусков Codex](../../reports/native/2026-09-19/REPORT_RU.md).
Это больше, чем review документов, но пока меньше, чем проверенный массовый релиз.

| Область | Состояние кандидата | Что ещё требуется |
|---|---|---|
| Продуктовая модель | Единый вход, три независимых измерения | Проверка понятности новичками |
| Исходная упаковка | Есть preview plugin, без scripts/hooks/MCP | Устанавливаемый versioned artifact после выбора прав |
| Repo connection | Отказ записи в `.agents` воспроизведён; исправлена частичная установка, сохранение файлов подтверждено | Успешные install/connect/reconnect/update/remove на поддержанном host |
| Frontend loop | Codex и Native исправили fixture; внешние browser checks прошли у обоих | Полный agent/browser цикл: в текущем CLI доступ заблокирован |
| Старт и режимы | Offline UI прошёл 48 сочетаний; plan/new-plan/backend/quick/review проверены реальным Codex | Свежие задачи, смена режима по ходу, usability |
| Static/repository checks | Фактические результаты в handoff | Не подменяют host/runtime trials |
| Desktop/CLI/IDE support | Кандидаты, разные browser capabilities | Заполнить матрицу реально испытанных hosts |
| Публичное использование | Не выпущено | Права, release checks, публикация |

Отсутствие public release, marketplace listing или лицензии не маскируется
инструкцией «просто установите». Ни один downstream пока не выбран и не изменён.

## 2. Три поставки вместо десяти стадий governance

### A. Подключение, которое можно проверить и отменить

**Выход:** один versioned Native package и краткая инструкция; цель первого
контакта — увидеть понятный setup diff и перейти к задаче без настройки процесса.

- Использовать текущие исходники `plugins/playbook-native/` как единственный
  источник skills. Выбрать один host-tested способ доставки plugin. Для CLI/IDE,
  где он недоступен, использовать те же repo-local `.agents/skills`.
- Перед публичной упаковкой решить права. Не копировать в Native старый набор
  tools/templates. Не публиковать все исследовательские архивы как install kit.
- Проверить install/connect/reconnect/update/remove в изолированных fixtures.
  Существующий `AGENTS.md`, root override, monorepo и локальные изменения должны
  переживать setup. Не менять global config или устанавливать tools без нужды.
- Проверить native discovery в новой сессии и отсутствие дубликатов skills.
  Наличие правильного `SKILL.md` само по себе этого не доказывает.
- Если agent-mediated merge регулярно ошибается, добавить маленький deterministic
  helper только для сохранения/обновления своего блока. Не писать installer
  framework до наблюдения проблемы.

Обнаруженный приоритет: подтвердить штатную установку plugin на чистом host.
Agent-mediated копирование в защищённую `.agents` не является универсальным
каналом доставки. Не лечить это отключением sandbox или новым prompts pack.

**Приёмка:** все non-destructive сценарии таблицы ниже выполнены; повторное
подключение не раздувает diff; удаление сохраняет проектные изменения. Нельзя
объявить Linux-tested пакет проверенным на Windows/macOS.

**Откат:** выключить plugin или убрать только установленный block/skill files;
не удалять пользовательские notes/tests. В preview уже описан этот контракт.

### B. Один полный цикл на реальном UI

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
[отчёте пилота](../../reports/native/2026-09-19/REPORT_RU.md). Сценарий без записи в отчёте
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
