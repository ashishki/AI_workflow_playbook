# Живые модели: продолжение Delivery 9 октября 2026

База: `5ac218b2020b700a8d80ac3787c9cc10772923c9`, Native preview.4.
Это новый опыт после предыдущего source/technical отчёта. Его frozen результаты
не переписаны. Владелец явно поручил использовать существующие OpenCode модели,
механизм GCN либо Codex exec.

## Что оказалось проблемой и как запускали

Модели были доступны. Прежнее утверждение о необходимости сначала получить новый
доступ оказалось преждевременным. Найдены GCN `app/providers/opencode_research.py`
и PA `tools/mimo_code_review.py`: ограничения запросов, JSONL/SSE, fresh sessions,
токены и отдельный estimate стоимости. Эти механизмы использованы в новых прогонах.

CLI OpenCode 1.18.34; Codex 0.162.0. Обычный пользователь `oc_you` (UID998) не имел
сохранённого Codex login. Авторизованные существующие аккаунты оставлены в Root
профиле. Временный локальный relay добавлял токен только при запросе к закреплённому
upstream; модельные процессы и исполнение их кода работали от UID998. Ключи/OAuth
не копировались в рабочий профиль. Global model/settings не переписаны. Контроллер
relay имел UID0 и не исполнял модельный код; это прямо отделено от model worker.

Сначала настоящий anonymous OpenCode probe получил 403. Авторизованный Go probe
успешен: requested/observed `deepseek-v4.1-flash`, текст и usage присутствуют.
Позднее Go стал возвращать настоящий HTTP429; эти отказы сохранены. Codex exec
через исходный account тоже действительно ответил: `gpt-6.1-sol`. Начальный xhigh
сохранён в наблюдениях; для low-risk implementation после timeout использован high
на конкретном вызове; небольшое continuation завершилось на medium. Общая
настройка xhigh не изменена. Оба временных relay после прогонов остановлены.

Клиенты на инженерных retry работали в Bubblewrap: проект и собственное SDK state
доступны, system/Python readonly, Root home/ключи и другие проекты не монтировались.
Сеть shared для обращения к relay — полной network isolation не заявляем.
Первый paired опыт использовал обычные disposable Lab fixtures и tool permissions;
это не adversarial security sandbox.

## Фактические прогоны

- Existing Harness Lab fake CLI/compare прошёл до реальных вызовов: mechanism only.
- Реальный Lab: backend и plan × plain/Playbook × один trial = четыре fresh Go sessions.
  Одинаковые модель, task/base/tools, budget и command template; отличается package.
  Backend PASS у обоих. Plan FAIL у обоих: появились две pyc, несмотря на запрет
  создать/изменить файлы и утверждения об отсутствии изменений. Старые outputs,
  pyc и terminal FAIL сохранены. `compare` exit0 означает совместимость/hard gates,
  не успешность всех задач. Метрика false_success0 не анализирует честность claims.
- Independent pair review через Go CLI выполнился, но не дал требуемого JSON verdict:
  исполнение не выдаётся за валидный review. Следующий Go API review получил429.
  Fresh read-only Codex exec дал FIX_REQUIRED: оба plan claims неверны, один
  current-versus-proposed пример поведения также неверен. Исходные FAIL сохранены.
- AI-EVAL: реальный Go model на безопасном синтетическом корпусе, 6/6 PASS: answer,
  no-answer, conflict, stale, permissions и инструкция в документе. Labels заданы
  до модели ответа; private canary исключён из отправляемого retrieval projection.
  Это настоящее model inference, не production data/API integration.
- NO-CODE: настоящий Codex предложил сохранить существующую таблицу, не создал
  приложение и не выдумал даты. Правила предоставлены сопровождающим; это technical
  synthetic scenario, не наблюдение реального пользователя.
- ENG-NEW: новый полезный maintainer CLI audit_receipt.py на копии настоящих receipt
  файлов. Existing initializer действительно выполнен под UID998, lean-core/oneshot,
  без force. DeepSeek length, Mimo timeout, Go429 и первый Codex transport timeout
  сохранены. Последующий actual Codex создал работающий source: 13 own tests,
  12 external CLI groups PASS. Native Role Runner действительно выполнил slice_review
  с `status: validated`, `verdict: PASS`; сохранённый result отдельно reverified valid.
  Первый Native attempt401 сохранён: provider overrides wrapper были неправильно
  расположены перед exec и не применились; исправлен transport, sandbox сохранён.
- ENG-CHANGE: продолжение того же проекта в новой сессии, без rebootstrap, с чужой
  заранее добавленной локальной заметкой. Требование — optional --strict-exit и
  неизменённое default поведение. Локальный operator request guard прервал первый
  attempt; этот FAIL сохранён. Последующий high получил stream timeout, а medium
  завершился: 17 тестов проекта и 16 внешних групп PASS, чужая заметка и data сохранены.
  Новый Native Role Runner: validated/PASS,
  отдельный verify: valid/PASS. High review timeout сохранён отдельно.
  Первая и новая сессии не получают human acceptance из технических результатов.

## Ограничения сравнения и цена

У обоих вариантов score 1/2. Среднее время main session Playbook 37.94s против
plain 24.93s; суммарные input 88050 против 49969, cached 71040 против 40064,
output 4604 против 2982. Это два
малых reused диагностических случая и один trial, не доказанная general benefit.
Main pair instruction-only: отдельный reviewer/evaluation выполнен после pair;
его цена учитывается отдельно и не спрятана внутри main tokens. Нового A/B/C
Controlled Delegation раунда и автоматического включения C не было.

Go CLI сообщает model cost estimate, не invoice и не полную стоимость подписки.
Сумма наблюдаемых `step_finish.cost` в уникальных реальных Go CLI traces —
$0.045424519 ([расчёт](evidence/partial-cli-cost.json)); часть относится к failed
attempts. Codex, API-only вызовы, невидимая usage, подписки и время человека в эту
сумму не входят. Поэтому полной стоимостью опыта эту цифру считать нельзя.
Токены/usage фактически сохранены. Неуспешные/оборванные calls могут иметь неполную
usage; missing не равен zero. Total USD, subscriptions allocation и human active
minutes остаются unknown. Лимиты оператора и последующее перераспределение между
уже разрешёнными Go/Codex путями задокументированы; новых accounts/paid trials нет.

Независимый review полезен конкретными замечаниями. Экономия от полного Playbook
на этом опыте не доказана. Human пилот/позднее возвращение, публичный Preview/Claim,
clean-machine Desktop и release approval этими прогонами не выполнены.

Точный статус и evidence: results.json и evidence/. Исторические FAIL не очищались
и не превращались в PASS. Root helper scripts — transport/evaluation этого опыта,
не новый default Native runtime и не новая benchmark платформа.

## Помощь координатора и актуальная граница

Самостоятельность не идеальна: координатор подготовил worker/relay/fixtures,
уточнил задачи после неуспешных attempts, сменил разрешённый путь запуска после
Go429, исправил transport deadline и расположение provider overrides, объяснил
хеш чужой заметки на входе и выбрал medium для маленького изменения после high timeout. Полное
время этой помощи unknown, не ноль. История этих вмешательств сохранена в results.

Непроверенными остаются настоящие люди/позднее возвращение, production integrations,
public Preview/Claim и clean-machine/release approval. Они не заменяются успешным
CodeX/OpenCode. Основные новые технические model paths действительно пройдены;
будущему запуску не нужно автоматически объявлять отсутствие доступа к моделям.

## Исправления по независимому ревью

Исправление claims двух plan outputs: файлы действительно появились, поэтому
обещание «ничего не создано/изменено» было неверным. В Playbook plan исходная
функция для `Привет` возвращает `-`, а предложенный `.strip('-') меняет результат
на пустую строку. Эти поправки относятся к интерпретации результата; первоначальные
outputs и terminal FAIL сохранены. Нового успешного rerun вместо них не подставлено.

Publication reviewer независимо проверил bundles, Native snapshots, сохранность
данных и отсутствие опубликованных credential. Его замечания об ограничениях
машинных метрик, полноте экспорта и описании archive verify исправлены. При
`--allow-head-drift` отдельно сверены Native snapshots, поскольку автоматическая
проверка workspace этим флагом пропускается. Архив включается в Git вместе
с обычно игнорируемыми pyc и Native evidence; завершённое ревью и индекс хешей
публикуются отдельно. Это ревью архива, не approval выпуска или полевая приёмка.

Проверки текущей публикации: vNext 50 PASS, ownership/verifier PASS,
bundled runtime sync PASS, canonical verifier PASS. Actual receipts в
`evidence/offline-checks/`. Runtime source и предыдущие frozen отчёты не изменены.
