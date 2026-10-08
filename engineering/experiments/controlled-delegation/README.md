# Controlled Delegation experiment

Эксперимент проверяет не «можем ли мы запустить много агентов», а приносит ли
управляемое делегирование добавочную пользу относительно сильных альтернатив.

## Текущий раунд

[Второй протокол](ROUND2_PROTOCOL_RU.md) задаёт 12 настоящих повторных A/B/C
прогонов на импорте продаж и решении о релизе, точные целые копейки, ограниченные
workers и общий независимый code review. [Отчёт второго раунда](../../../reports/delegation/2026-10-08-round2/REPORT_RU.md)
раскрывает первые попытки, repairs, неполные проверки, реальные diagnostic probes
и неизмеренные USD/активные человеко-минуты. Первый раунд ниже заморожен.

## Сравниваемые условия

- **A — ordinary Codex:** без Playbook-специфичной оркестрации; host работает как обычно.
- **B — Playbook, single session:** тот же Playbook, но task work выполняет основной агент.
- **C — Playbook, Controlled Delegation:** маршрутизация self/delegate/ask/stop,
  максимум 3 parallel workers и depth=1.

Модель, reasoning, permissions, исходные файлы, порядок помощи и бюджет должны быть
одинаковыми. Порядок прогонов рандомизируется. Каждое условие запускается в отдельном
workspace и новой host-session.

## Подготовка

Из корня репозитория:

```bash
python engineering/experiments/controlled-delegation/evaluate.py prepare \
  --output .playbook-artifacts/controlled-delegation \
  --head "$(git rev-parse HEAD)" \
  --model "<точная модель>" \
  --host "codex"
```

Команда ничего не отправляет модели. Она создаёт 15 изолированных workspaces,
`run-plan.json` и пустой `results.json`. Условия B/C получают одну и ту же копию
skills; A не получает Playbook.

Следуйте порядку из `run-plan.json`. В каждом workspace откройте `TASK.md`. Перед
завершением агент должен создать `run-result.json` по шаблону и сохранить реальные
логи/receipts внутри workspace. `PASS` без существующего evidence не принимается.

`task_status` отделяет наблюдаемый результат задачи от полной приёмки эксперимента.
`usage_complete` требует фактических полных counters, включая workers/review; при
отсутствии подтверждения оставьте null. Записывайте implementation/research и review
counts отдельно. Не превращайте отсутствующий cost/usage в PASS только потому, что
тесты зелёные. Для ENABLE нужны завершённые A/B/C и сопоставимые outcome scores;
если заранее определённой шкалы нет, score остаётся null и capability не включается.
Подтверждения fresh-session/worker detection — только boolean true/false или null.

## Механическая проверка и отчёт

После прогонов:

```bash
python engineering/experiments/controlled-delegation/evaluate.py collect \
  --run-root .playbook-artifacts/controlled-delegation \
  --output .playbook-artifacts/controlled-delegation/collected-results.json

python engineering/experiments/controlled-delegation/evaluate.py report \
  --input .playbook-artifacts/controlled-delegation/collected-results.json \
  --output-dir reports/delegation/2026-10-08
```

`collect` выполняет только детерминированные acceptance checks и понижает ложный
PASS до FAIL. `report` не читает raw chats и не утверждает причинность; он формирует
`REPORT_RU.md`, нормализованный `results.json` и решение:

- `ENABLE_CONDITIONALLY`;
- `KEEP_EXPERIMENTAL`;
- `REVISE_OR_REJECT`.

## Что измеряем

- outcome score и критические ошибки;
- wall time и время участия человека;
- стоимость/tokens, когда host их действительно показывает;
- число subagents, max parallel и depth;
- owner checkpoints и лишние approvals;
- write conflicts;
- обнаружение ошибочного/противоречивого worker;
- fresh-session continuation.

Agent count и длительность сами по себе не являются успехом.

## Что не доказывает эксперимент

Даже хороший результат не доказывает пользу для любой модели, профессии или
долгой production-работы. Он только решает, стоит ли включать capability условно
и на каких классах задач. Пользовательский эффект проверяется отдельно.

Короткий VPS-промпт находится в [VPS_PROMPT_RU.md](VPS_PROMPT_RU.md).
