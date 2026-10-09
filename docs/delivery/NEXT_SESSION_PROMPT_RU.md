# Следующая сессия: продолжать по фактам

Работаем в AI_workflow_playbook. Прочитай AGENTS.md, docs/vnext/STATUS.md,
docs/delivery/PLAN_RU.md и reports/delivery/2026-10-09/REPORT_RU.md / results.json.
Затем новый reports/delivery/2026-10-09-live-models/REPORT_RU.md / results.json.

Техническая проверка и model отчёт слиты в master через PR #13, merge `d003bf7`;
все три CI этого коммита PASS. Ветка проверки — feature/delivery-acceptance-20261009.
Получить фактический remote HEAD перед работой; не принимать исторический SHA
за текущий. Runtime source 7f36b90 проверен, preview.4.
Preserve frozen reports, original отрицательные результаты и чужие изменения.

D00/dev/source CI уже исправлен. Не пересоздавай исторический July host/approval
и не повторяй vNext migration. Результаты Controlled Delegation сохранены, default
runtime C не включён. ZIP/GUI/HTTP/browser/synthetic transfer technical checks
имеют реальные receipts; synthetic teacher/demo identity не являются field pilot.

Технические model маршруты ENG-NEW/ENG-CHANGE/ENG-EXP, NO-CODE и AI-EVAL фактически
пройдены. У обоих инженерных source состояний настоящие Native slice_review и
verify PASS. Plain/Playbook main pair: backend PASS обоих, plan FAIL обоих;
сохранены pyc, ложные claims, invalid review/429/timeouts, вся помощь координатора.
Первый незавершённый полный шаг D02 остаётся ограничен самостоятельностью/полной
историей, а не отсутствием модели. Не повторяй автоматически все технические
маршруты и не записывай их сразу как full D02/D03/D06–D08 PASS.

Рабочие существующие CLI: OpenCode Go (`deepseek-v4.1-flash`, peer GLM/Mimo) и
Codex exec (`gpt-6.1-sol`). Read-only GCN mechanic —
`../Georgia-Community-Navigator/app/providers/opencode_research.py`;
PA bounded SSE — `../telegram-research-agent/tools/mimo_code_review.py`.
Модельные процессы UID998; исходные ключи/OAuth не копируются. Временный relay
закреплял upstream и добавлял credential в Root только для transport; он остановлен.
Это механизм опыта, не новый default runtime. Проверять текущую доступность/лимиты;
Go реальный429 не обходить, глобальные model settings не менять скрытно.
Root exception из R3 не переносится на Delivery. Полная цена и human time unknown.

D09 требует настоящего позднего использования/изменения, не симуляции.
Public preview/account/Terms/claim и release/distribution требуют применимых прав.
D10 clean-machine W/M/L и owner release decision не получены из matrix CI.

Следующий согласованный шаг описан в PLAN_RU.md, раздел «Следующий рабочий шаг:
одна настоящая задача», и product/pilots/README.md. Статус NOT RUN: конкретные
участник, проблема и разрешённые примеры ещё не зафиксированы. В начале сессии
получить от владельца: что сейчас неудобно, как это делают сегодня, какой результат
нужен и какие данные можно использовать. Пока этих фактов нет, не выдумывать кейс.

Далее записать исходный способ и метрику; довести достаточное решение до реального
использования; после настоящего интервала участник просит изменение в новой
сессии. Проверить сохранность и передачу, сравнить пользу и полные затраты,
отдельно записать всю помощь автора. Результатом может быть таблица или правило.
Возврат через несколько дней не заменяет ещё не наблюдавшуюся неделю/месяц.
Production интеграции, public Preview/Claim и чистые машины выполнять по очереди
до соответствующего внедрения/выпуска; model/synthetic PASS их не закрывает.

Отмечай PASS/FAIL/NOT RUN только по наблюдениям. Исправление процедуры, git merge
и работающая локальная репетиция не являются доказательством production пользы.
