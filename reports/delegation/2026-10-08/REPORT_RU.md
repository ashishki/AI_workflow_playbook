# Controlled Delegation — отчёт эксперимента

Experiment: `controlled-delegation-2026-10-08`
HEAD: `85180b0b1b1ad60f842ee1e02ddf1f4da89c23c9`
Model/host: `gpt-6.1-sol` / `codex-cli-0.160.1`

> Ограниченный эксперимент: не универсальное доказательство multi-agent и не бизнес-пилот.

## Сводка

| Условие | PASS | FAIL | BLOCKED/NOT RUN | Outcome | Human min | Cost USD | Subagents |
|---|---:|---:|---:|---:|---:|---:|---:|
| A: ordinary_codex | 0 | 1 | 4 | — | — | — | 0.20 |
| B: playbook_single_session | 0 | 1 | 4 | — | — | — | 0.60 |
| C: playbook_controlled_delegation | 0 | 3 | 2 | — | — | — | 1.40 |

## По сценариям

| Сценарий | A | B | C | C agents/depth/checkpoints | Mechanical |
|---|---|---|---|---|---|
| small_fix | FAIL | FAIL | FAIL | 1/1/0 | PASS |
| parallel_research | BLOCKED | BLOCKED | FAIL | 3/1/0 | PASS |
| medium_implementation | BLOCKED | BLOCKED | BLOCKED | 1/1/0 | PASS |
| conflict_detection | BLOCKED | BLOCKED | FAIL | 1/1/0 | PASS |
| fresh_session | BLOCKED | BLOCKED | BLOCKED | 1/1/0 | PASS |

## Решение

**REVISE_OR_REJECT**

- Есть FAIL в Controlled Delegation.
- Есть критические ошибки или конфликты записи.
- Нарушена граница implementation/research workers: conflict_detection.

## Что ещё не доказано

- перенос на другие модели/hosts/задачи;
- стоимость и внимание на реальной длительной работе;
- удобство для нетехнического владельца процесса;
- depth > 1;
- полезность ежедневных автоматизаций как отдельного runtime.

Raw traces остаются локально в experiment workspaces.

## Реальные прогоны и полная приёмка

Все 15 workspaces запускались в порядке `run-plan.json`. Всего 18 новых `codex exec` сессий (fresh_session имеет две фазы) и 11 native subagent threads. Ни один A/B/C-прогон не заменён имитацией. Механическая приёмка: **15 PASS / 0 FAIL / 0 NOT RUN**. После проверки процесса, независимых findings и одинаковых post-hoc probes: **11 PASS / 4 FAIL** по результату задачи. Квалификация эксперимента: **0 PASS / 5 FAIL / 10 BLOCKED / 0 NOT RUN**. BLOCKED означает отсутствие обязательных измерений, а не отсутствие реального запуска.

Исходные agent claims сохранены в `agent_reported_status` и локальных `agent-run-result.json`. Итоговые статусы выставлены оператором по receipts. `outcome_score` остаётся null: заранее определённой шкалы не было.

| Сценарий | Задача A/B/C | Wall A / B / C, секунд | C implementation / review |
|---|---|---:|---:|
| small_fix | FAIL / FAIL / FAIL | 117.585 / 409.585 / 252.634 | 0 / 1 |
| parallel_research | PASS / PASS / FAIL | 66.700 / 88.677 / 600.128 | 3 / 0 |
| medium_implementation | PASS / PASS / PASS | 181.043 / 206.775 / 523.134 | 0 / 1 |
| conflict_detection | PASS / PASS / PASS | 87.502 / 94.230 / 137.687 | 1 / 0 |
| fresh_session | PASS / PASS / PASS | 272.966 / 377.050 / 358.876 | 0 / 1 |

C соблюдал max parallel=3, depth=1; recorded owner checkpoints=0 и write conflicts=0. Все защищённые исходные task/test files сохранили начальные hashes. Native reviewers работали по read-only контракту, но наследовали workspace-write sandbox; аппаратная/ОС-изоляция чтения в этих workers не доказана. Финальное ревью запускается отдельно с read-only sandbox.

## Findings и исправления

- `small_fix` A/B/C: одинаковые проверки на 1e15, 1e16 и максимальном finite float воспроизвели потерю денежной точности и infinity. B/C reviewer обнаружили проблему до окончания своих сессий и оставили BLOCKED; A заявил PASS по ограниченным тестам. Post-hoc проверка понизила A до FAIL. Это польза независимой проверки Playbook, а не доказательство пользы делегирования относительно B.
- `parallel_research` C: три worker вернули правильные факты, decision и evaluator PASS. Дополнительный review через follow-up существующего constraints worker не вернулся; общий лимит 600 секунд исчерпан. Сессия не получила turn.completed, хотя после SIGTERM процесс вернул exit 0. Итог FAIL; counters C в этом сценарии частичные.
- `conflict_detection` C: правильное решение и нормальная завершённая сессия, но один research/audit worker при min=2 в suite. Полная квалификация FAIL. Минимум отсутствовал в явных AGENTS/TASK инструкциях; исправлен prepare для будущих запусков, frozen inputs не переписаны.
- Во всех условиях противоречие было между stale-файлом и текущими facts. Реально ошибочный уверенный ответ model-worker не внедрялся. Поэтому `failed_or_conflicting_worker_detected=false` для C conflict_detection сохранён; fault-injection сценарий остаётся NOT RUN.
- Исправлен evaluator: пустой workspace/ноль тестов и изменённые fixtures больше не получают PASS; проверяются explanation/business fields и old_behavior flag; reviewers отделены от implementation workers; min/max bounds и usage/cost проверяются; подтверждённый FAIL больше не скрывается другим BLOCKED. Добавлены source regression checks.
- Уточнён delegation reference: deadline входит в общий бюджет, follow-up не сбрасывает его, потерянный return должен останавливать bounded workstream; text-only решения не требуют дополнительного ceremonial review. Эта версия reference создана после сравнительных прогонов.
- Отдельная попытка исправления float-конверсии находится в `repair_attempts/attempt-1/`: три исходных reproduction cases PASS, но расширенные regressions дали 7 failing subcases. **FAIL, не принято.** Тип результата и область валидных сумм не были изменены ради зелёного статуса. Numeric defect исходных решений остаётся незакрытым; надёжный monetary contract требует отдельного решения о точном типе/домене.

## Стоимость и участие владельца

Фактическая USD-стоимость: **NOT RUN / null** — ChatGPT-authenticated host не дал billing receipt. Время активного участия владельца: **NOT RUN / null**; отсутствует измерение, экономия не заявляется.

| Условие | Сумма wall, с | Input tokens | Cached input | Output tokens | Native workers всего |
|---|---:|---:|---:|---:|---:|
| A | 725.796 | 793021 | 658176 | 24138 | 1 |
| B | 1176.317 | 1792070 | 1548928 | 37967 | 3 |
| C | 1872.459 | 2173863 | 1935232 | 40168 | 7 |

Всего наблюдается **не менее 4 758 954 input и 102 273 output tokens**, включая отдельные native child counters. C parallel_research прерван: его counters — нижняя граница. Токены координирующего Codex, source analysis, post-hoc repair и финального ревью не включены в A/B/C; end-to-end стоимость неизвестна. Cached/input/output нельзя превратить в фактические USD без billing evidence.

Сумма wall C — 1872.459 с против B 1176.317 с (1.59×) и A 725.796 с. В fresh_session C немного быстрее B, но для medium_implementation C выбрал self и использовал только reviewer. В малой задаче B/C различается время неуспешных попыток, а не доказанный quality gain. Один повтор и фиксированный порядок не позволяют приписать разницу исключительно делегированию.

## Source checks, CI и evidence

| Проверка | Статус | Evidence |
|---|---|---|
| `python3 -m unittest discover -s tests/vnext -p 'test_*.py' -v` | PASS | [vnext-after.log](evidence/vnext-final.log) |
| `python3 tools/vnext_check.py --root .` | PASS | [vnext-check-after.log](evidence/vnext-check-final.log) |
| `python3 -m unittest discover -s distribution/native -p 'test_*.py' -v` | PASS | [native-after.log](evidence/native-after.log) |
| `python3 -m unittest discover -s distribution/desktop -p 'test_*.py' -v` | FAIL | [desktop.log](evidence/desktop.log) |
| `python3 distribution/native/sync_runtime.py --check` | PASS | [sync-after.log](evidence/sync-final.log) |

Native: один permission test NOT RUN (root обходит Unix read-only bits). Desktop: один тест FAIL из-за отсутствия tkinter. GUI readiness не доказана; установка системного GUI runtime в задачу не добавлялась.

CI до эксперимента относится к исходному HEAD 85180b0: [Playbook vNext](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37754295613), [Native Product Checks](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37754295560). CI будущего pushed commit ещё не наблюдался на момент подготовки отчёта; его статус сообщается отдельно после push.

Raw logs: `.playbook-artifacts/controlled-delegation/` (локально, не в Git). Публичные синтетические outputs, session IDs, settings, usage и SHA-256 receipts: [evidence-index.json](evidence-index.json) и `evidence/*.json`. Точные operator scripts: `evidence/operator/`. Исходный checker — frozen `.evaluation/` каждого workspace; report/collect после safety fixes применены одинаково ко всем.

## Ограничения вывода

Одна модель gpt-6.1-sol, reasoning high, CLI 0.160.1, стандартная библиотека Python 3.10.12, очень маленькие fixtures, один запуск на пару. Baseline не ослеплён: одинаковая локальная копия evaluator содержит suite. Native Role Runner не выполнялся: scoped reviewers запускались native host tools. Phase 2 fresh_session — новый exec без resume/fork и старого chat; на диске лежат phase-1 traces, но по наблюдаемым командам они не читались как прежний chat. Производственный downstream, другие hosts, платные интеграции и rollout не проверялись.

**Вывод: добавочная польза Controlled Delegation относительно B не доказана. REVISE_OR_REJECT означает переработку и повторную проверку capability, а не универсальный запрет делегирования.** Нужны надёжный bounded return/review, явные worker bounds, корректный monetary fixture contract, повторные A/B/C наблюдения, реальный fault injection и измеренные cost/owner time. Нативный запуск нескольких worker сам по себе этих доказательств не даёт.

Финальное независимое read-only ревью **COMPLETED, исходный вердикт STOP_SHIP**. Reviewer подтвердил честность evidence/выводов и нашёл обходы evaluator. Они исправлены и проверены source regressions. Повторное независимое ревью исправленного состояния — **NOT RUN** (один итоговый reviewer по VPS-протоколу). См. [INDEPENDENT_REVIEW_RU.md](INDEPENDENT_REVIEW_RU.md).

После независимого ревью закрыты три группы findings: FAIL задачи/механики имеет приоритет; incomplete usage, незавершённый A baseline и отсутствующие quality scores блокируют ENABLE; строковые boolean confirmations отклоняются. Дополнительно воспроизведён и закрыт NaN/Infinity metrics bypass. Source checks PASS; это не независимое одобрение нового diff и не live-доказательство новой версии capability.

Финальное ревью расходовало отдельно 758 999 input (671 744 cached) и 9 239 output tokens, wall 318.920 с. Наблюдаемый subtotal A/B/C + review: **≥5 517 953 input / 111 512 output tokens**; координирующий агент не измерен, фактические USD остаются неизвестными.

`critical_errors` сохраняет исходные агентские counters: C small_fix сообщил 1, A/B — 0 при том же численном дефекте. Общая severity rubric не была определена; эти counters не используются как сопоставимый quality score. Решение REVISE_OR_REJECT уже обосновано подтверждёнными FAIL и нарушением worker bound.
