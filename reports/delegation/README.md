# Controlled Delegation reports

Отчёты здесь создаются только после фактических A/B/C-прогонов из
`engineering/experiments/controlled-delegation/`.

До запуска не добавляйте заполненный `REPORT_RU.md` или PASS-статусы. Генератор
сохраняет нормализованный `results.json`, механические проверки и рекомендацию:
`ENABLE_CONDITIONALLY`, `KEEP_EXPERIMENTAL` или `REVISE_OR_REJECT`.

Raw agent chats/traces остаются в `.playbook-artifacts/` и не коммитятся. В Git
попадают только обезличенный итог, ссылки на локальные/CI evidence и честные
`NOT_RUN/BLOCKED` для недоступных проверок.
