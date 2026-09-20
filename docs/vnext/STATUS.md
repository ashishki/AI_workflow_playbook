# vNext — фактическое состояние

База переработки — `1e0abe0048daefc30d2f7f9276ab12246bda6856`; до текущего
незакоммиченного исправления проверенный HEAD —
`0a164c5e4efdf7c07ad660676bd4af208e45d236`. Ветка
`feature/playbook-vnext-20260919`; [PR №9](https://github.com/ashishki/AI_workflow_playbook/pull/9).
Это переработка репозитория и частная техническая проверка, не завершённый
внешний пилот или релиз.

## Реализовано

Два действующих входа: Engineering для новых/текущих реальных проектов и
отдельных экспериментов, Product — для полного пути владельца рабочей проблемы.
Shared задаёт общие реализации и явную карту владельцев. Исходные
runner/frontend/Governed сохранены по совместимым путям. Все tracked-пути
классифицированы, 50 прежних компонентов сопоставлены с жизненным циклом, а все
13 стадий доступны как вызываемые процедуры и входят в архив.

Необязательный solution record проверяет структуру и внутреннюю согласованность,
показывает итог, фиксирует выбранные файлы и обнаруживает устаревание перед
передачей. Команды из записки не исполняются. Версия пакета —
`0.2.0-preview.1`; старые продуктовые документы, frozen evidence, master,
текущие downstream и права распространения не менялись.

После implementation review усилен Native builder. До создания ZIP он отвергает
непереносимые или извлекаемые за корень имена, включая Windows-разделители,
traversal, device/control forms и normalisation/case collisions. Производные имена
архива проверяются как ограниченный SemVer. ZIP и checksum строятся в приватной
staging-директории, публикуются без замены через hard link и перепроверяются.
Финальные файлы намеренно read-only. Это защита обычной локальной private-evaluation
сборки, а не новый контракт против конкурирующего процесса с той же учётной
записью.

## Наблюдённые проверки

Исторические CI для `0a164c5` остаются в [PR №9](https://github.com/ashishki/AI_workflow_playbook/pull/9),
но не приписываются автоматически текущему незакоммиченному изменению builder.
На текущем дереве локально прошли:

- `python3 -m unittest discover -s tests/vnext -v` — 29 PASS.
- `python3 -m unittest discover -s distribution/native -p 'test_*.py' -v` —
  24 tests, из них один permission test skipped, потому что процесс запущен от
  root и root обходит Unix read-only mode.
- `python3 distribution/native/sync_runtime.py --check` — `Runtime copies: current`.
- `python3 tools/vnext_check.py --root .` — `contracts_valid`; также прошли
  `python3 -m py_compile distribution/native/build.py` и `git diff --check`.

Независимые read-only Role Runner reviews сохранены локально в ignored
`.playbook-artifacts/runs/` и валидированы командой `run_codex_role.py verify`:

- `vnext-20260920-architecture`: gpt-5.6-terra/high, PASS, inspected HEAD
  `0a164c5`; подтверждённых дефектов архитектуры не найдено.
- `vnext-20260920-implementation`: gpt-5.6-luna/medium, ADVISORY, inspected
  `0a164c5`; подтвердил риск ZIP path traversal через обратные слеши в имени
  исходного файла. Риск исправлен выше и покрыт регрессиями.
- `vnext-20260920-consolidated-security-astra`: gpt-6-astra/high, PASS,
  inspected полный двухфайловый working-tree delta относительно `0a164c5`.
  Он не нашёл in-scope blocker после исправления. Review отдельно оставляет за
  границей контракта malicious same-identity filesystem races и не подтверждает
  файловые системы без hard links или multi-OS CI текущего delta.

Запуск `vnext-20260920-security-fix-final` на terra не был завершён из-за
`Selected model is at capacity`; согласно процедуре повторный сложный security
review был выполнен на gpt-5.6-sol/high до финальной consolidated проверки.

## Реальные Codex trials

Сначала механический preflight проверил подстановку командного шаблона Harness Lab;
он не считается trial. Затем на свежих одинаковых booking fixtures действительно
запущены два single-attempt Codex execution (`codex-cli 0.155.1`,
gpt-6-astra/high, timeout 330 s): plain baseline и Product/playbook. Оба bundle
прошли `verify-bundle`, не timeout, без parser errors, nested reviews и policy
failures; независимый `external_acceptance:1.0.0` дал каждому score `1.0`.

`comparison_report.json` в
`.playbook-artifacts/native-lab/vnext-20260920-real-booking/comparison/` имеет
статус `empirical comparison`: по одному valid run на условие, zero detected
false successes/policy violations. Baseline: 204.524 s, 181763 input / 5399
output tokens, 8 tool calls. Playbook: 199.786 s, 181938 input / 5750 output
tokens, 11 tool calls. Стоимость неизвестна. Один sample на условие не даёт
оснований заявлять стабильность, превосходство, снижение стоимости или пользу
человеку; zero detected violations ограничен покрытием данного scorer.

## Что не завершено и почему

M0–M4 реализованы как модель, маршруты, классификация, библиотека и helpers.
M5–M6 всё ещё ожидают реального случая и мини-группы по протоколам в
`product/pilots/`: настоящего владельца, последующего изменения, передачи без
автора, диагностики/восстановления и наблюдения эффекта. Техническая пара
Codex trials не заменяет эти проверки.

Не выполнены CI и ручная Windows/macOS проверка именно текущего builder delta;
совместимость output filesystem без hard links не доказана. Нет внешней
публикации, аккаунтов, участников, платных подписок, production-данных или
установок у пользователей. PR остаётся draft и не слит.

## Продолжение и откат

После push посмотреть CI именно нового commit; затем, только при отдельном
разрешении, провести реальный Product-кейс и последующее изменение/передачу без
автора. Не включать таймеры, не приглашать участников и не менять
model/master/downstream без применимой задачи.

Rollback — revert vNext-коммитов. Production-данные и установленные у
пользователей решения не менялись; локальные `.playbook-artifacts` —
диагностическое evidence, не публичный релиз.
