# Controlled Delegation — третий раунд: preregistration

Предыдущие два раунда, включая первые ошибки, frozen outputs и отчёты, остаются
неизменными. Этот отдельный эксперимент проверяет пользу делегирования для одной
более крупной debugging-задачи с тремя независимо исследуемыми подсистемами.
Исходники `round3*.py`, этот протокол, используемые round2 host/counter adapters,
рубрикa, inputs, skills и run order закрепляются до первого model call.
Implementation source/tests не являются доказательством live успеха.

## Задача и одинаковая проверка

Синтетический репозиторий fulfillment replay содержит реальные три дефекта в
inventory, checkout и refunds. Существующие public tests/fixtures и дополнительная
одинаковая operator behavioral+structured-diagnosis verification проверяют как
исправления, так и понимание причины, без per-run model reviewer.
Точные группы/веса доступны в `round3_fixtures.py` и `run-plan.json`; сумма 100.
Все A/B/C получают одинаковые task/data/tests/src; hidden evaluator/expected
answers не копируются в рабочий каталог. Полное качество: 100 и все группы PASS.

До operator imports и после работы проверяются SHA protected files; symlinks,
удалённые исходники и неожиданные добавленные файлы дают FAIL без выполнения
workspace evaluator. Разрешены изменения только существующих `src/**/*.py` и
создание/изменение `diagnosis.json`, `STATE.md`. Новые Python helpers, cache,
sitecustomize/conftest, другие tests, skills, git metadata запрещены. Operator
hidden evaluator запускается в isolated Python вне workspace evaluator paths.
STATE содержит Rules, Verification, Limits, Next step и только реальные checks.
Guard не доказывает отсутствие промежуточных изменений, восстановленных до check,
и не является полной защитой от произвольного поведения изменённого source code.

## A/B/C и бюджет

Шесть основных запусков, A/B/C × два повтора. Выполняются последовательно в
изолированных каталогах; порядок внутри каждого повторa randomized seed=20261008
и фиксируется до calls. Model gpt-6.1-sol, reasoning high, одинаковые host flags,
workspace-write permissions, no network/accounts/dependency installs/commit/push.
A — ordinary host behavior без Playbook; может естественно выбрать native workers
при тех же ограничениях. B — Playbook и один implementation agent.
C — Playbook и обязательные 2–3 настоящих read-only native analysis workers;
main остаётся единственным writer. B/C получают одинаковые skill files.
C проверяет выбранный класс задач с forced delegation, а не automatic routing.

Main получает 600 секунд включая свои checks. Host реально прекращает process
через deadline (SIGTERM, затем ограниченный grace/SIGKILL); elapsed раскрывается.
Каждый worker получает scoped message с `[R3_READ_ONLY]`, subsystem scope,
`180 seconds`, запретом writes/nesting/reviews/network, fork_turns=none,
без model/reasoning override. Maximum parallel 3, depth 1, без reuse/followups
completed workers. Main наблюдает и interrupt overdue worker; реальные child
intervals проверяются после завершения, >180 секунд дают protocol FAIL,
missing endpoints/counters — BLOCKED. Это instruction+observed postcheck,
не отдельный OS-enforced 180-second worker timer.

Worker sandbox наследуется от main. Read-only означает scoped instruction и
наблюдаемое соблюдение, не OS read-only proof. Known write tools в actual child
trace дают FAIL; tool inventory раскрывается. Shell/Python могут писать без
known write tool: этот guard не доказывает отсутствие таких writes. Protected
hashes и addedfiles guard применяются ко всему workspace. Никаких reviewers в
main/worker task. Единственная first attempt, без repair/повторного feedback.
Timeout/errors сохраняются; нет simulation fallback и evaluator runtime edits.

## Измерения и решение

Task outcome требует полного одинакового deterministic score и завершённого
host. Фактически подтверждённый defect/guard violation — FAIL; incomplete
execution/verification без подтверждённого defect — BLOCKED. Protocol outcome
отдельно требует реальные child receipts, settings, bounds и counters.
Input/cached-input/output counters суммируются по persistent provider thread
streams main + actual children без double count CLI summary. Missing counters,
unfinished thread/deadline или unknown settings не выдаются за complete. USD без
billing receipt и active human minutes без участия человека остаются null.

Preregistered signal **потенциальной пользы только на этом сценарии**:
обе C task/protocol PASS; качество C не ниже соответствующей B; обе B также
завершены и protocol PASS для сопоставимого времени; median implementation wall
C/B ≤0.80; полные summed uncached-input и output ratios C/B каждый ≤2.0.
Другие исходы — no shown benefit/mixed либо BLOCKED при missing measurements.
Wall raw ratio failed/capped attempts публикуется лишь описательно, без speedup
claim. Отдельно раскрываются каждый повтор, A outcome, first attempt и token
completeness. n=2 одного synthetic case не статистический результат.
Full qualification остаётся BLOCKED при неизвестных USD/human minutes.
Никакого production enable или разрешения rollout из batch.

## Отдельный independent review и среда

После всех шести прогонов оператор выполняет один настоящий независимый общий
review source/outputs/report. Он не входит в individual task outcomes, task wall
или task token ratios и не называется per-run code review. Review привязывается
к immutable snapshot manifest (sources, шесть receipts, outputs, report до
review), SHA snapshot и actual reviewer artifact/trace hashes. Review receipt
вне snapshot и позже входит в final evidence-index, без circular hash binding.
До реального review его статус BLOCKED, результаты не выдумываются.

`execution_context` в plan фиксирует uid/user/host; operator обязан раскрыть
выбранную авторизованную среду и исключение, если использован root вместо
рекомендованной VPS среды. Подготовка не разрешает перенос account/auth или новые
permissions. Model calls запускаются только после отдельной авторизации owner.

## Команды и артефакты

    python3 engineering/experiments/controlled-delegation/round3.py prepare --root .playbook-artifacts/delegation-round3/runs --head <prepared-source-SHA>
    python3 engineering/experiments/controlled-delegation/round3.py run --root .playbook-artifacts/delegation-round3/runs
    python3 engineering/experiments/controlled-delegation/round3_report.py --root .playbook-artifacts/delegation-round3/runs --output reports/delegation/2026-10-08-round3

No overwrite frozen evidence. Public report содержит sanitized receipts, реальные
synthetic outputs, actual frozen source copies и SHA index. Raw chats/session
streams остаются локально; partial logs/receipts не удаляются и не заменяются.

Подготовленный uid=0 plan без явного ответа owner имеет
`authorization=PENDING_ROOT_EXCEPTION`; `run` блокируется до provider setup.
Такой preflight содержит шесть `execution_status=NOT_RUN` / BLOCKED и не
занимает destination final live report. После явного исключения нужен новый
prepared root с `--root-exception-authorized`; старый pending plan сохраняется.

После фактического batch сначала publish в отдельный draft destination, затем:

    python3 engineering/experiments/controlled-delegation/round3_report.py --root <actual-runs> --output <published-draft> --snapshot-for-review

Это сохраняет `common-review/snapshot.json` (sources, все шесть receipts/outputs,
pre-review report hashes). Настоящий reviewer получает этот immutable snapshot.
После actual review оператор сохраняет `common-review/receipt.json` с полями
`status=validated`, `actual_provider=true`, `scope=common_source_output_report`,
`snapshot_path`, `reviewed_snapshot_sha256`, `review_started_utc`,
`review_finished_utc`, `artifacts` (path/sha256/kind; реальные `provider_trace`
и `report`). Финальная публикация в новый destination проверяет hashes,
покрытие всех шести runs и after-batch timing. Raw provider trace не публикуется,
его actual SHA остаётся в receipt. До этих артефактов common review BLOCKED.

Фактический размер текущего fixture: 67 task files включая TASK, 44 source files,
527 source lines; medium synthetic connected repository. Diagnosis points
проверяют структурную привязку causal paths/current event+trace/stale exclusion и
наличие prose. Семантическая правдивость prose не доказана автоматическим score;
её оценивает отдельный настоящий общий source/output/report review.
