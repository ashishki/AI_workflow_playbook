# Как проверить сохранённые результаты

Это архив actual runs поверх `5ac218b`, не команды для бесплатной повторной
генерации. Восемь Lab bundles включают четыре mechanism calibration и четыре
реальные Go model sessions. Наблюдаемые pyc сохранены намеренно: два real plan
получили FAIL именно из-за файловых изменений. Не очищать их перед проверкой.

Из корня Playbook с установленными `requirements-dev.txt`:

```bash
.venv/bin/python -m unittest discover -s tests/vnext -v
.venv/bin/python tools/vnext_check.py --root .
.venv/bin/python distribution/native/sync_runtime.py --check
```

Для каждого каталога `lab/{mechanism,real}/{baseline,playbook}/{backend,plan}/trial-0`
вызвать существующий `ai_workflow_harness_lab.evidence.verify_bundle(path)`.
PASS bundle integrity не меняет scorer FAIL задачи. `evidence-index.json` хранит
SHA256 всех файлов архива, кроме самого индекса и финального publication review:
review записывает проверяемый индекс отдельно, чтобы избежать кругового хеша.

Две копии проектов: `outputs/eng-new` до continuation и `outputs/eng-change`
после него. Их actual Native result paths перечислены в `results.json`. Для
проверки копии: `tools/run_codex_role.py verify --root <copied-project> --result
<actual-result.json> --allow-head-drift`. Флаг допустим здесь только потому, что
архив не содержит `.git` исходного disposable проекта и наследует иной Git HEAD.
Флаг проверяет сохранённые artifact bindings, но пропускает inherited HEAD и
автоматическую проверку актуальности workspace snapshot. Поэтому для архива
обязательна отдельная проверка: текущий `native_snapshot` копии точно равен
`workspace_snapshot` сохранённого результата. Independent reviewer действительно
выполнил обе проверки. Live runner и live verify выполнялись без флага; прежний
review после изменения source уже неактуален.

External CLI проверки в `sources/external_*_acceptance.py`; actual logs в
`evidence/eng-{new,change}-independent.*`. 13/17 model-written tests не заменяют
12/16 внешних групп. Исполнение полученного от модели кода выполнялось UID998.

В `sources/` сохранены временные adapters, ограниченные relays и wrapper.
В них есть абсолютные пути этого VPS; это provenance, а не готовая установка
для другого владельца. Private relay configs и исходные credentials отсутствуют.
Relays остановлены. Новые inference calls требуют текущего разрешённого доступа,
лимита и новой сессии; failure нельзя задним числом заменить PASS.

Фактические расходы разделены: `evidence/partial-cli-cost.json` считает только
видимый Go CLI estimate; ledgers хранят реальные requests/usage. Total USD,
подписки, missing usage и помощь человека остаются unknown.
