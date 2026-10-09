# Controlled Delegation — третий раунд

Наблюдённый batch: **BLOCKED**. Полная qualification: **BLOCKED**. Сигнал сценария: **BLOCKED_INCOMPLETE_MEASUREMENTS**. Production enable: нет.

Одна средняя синтетическая debugging-задача, три независимо исследуемые подсистемы; A/B/C × 2, шесть последовательных первых попыток. Repair отсутствует. Модель gpt-6.1-sol/high, одинаковые runtime flags, main 600 секунд с host deadline. Worker 180 секунд — scoped instruction и фактическая postcheck длительность, без OS read-only гарантий. A выбирает обычный host behavior с возможными native workers, B — Playbook/один агент, C — Playbook/обязательные 2–3 native workers и main sole writer.
Фактический размер fixture: 67 файлов, 44 source files, 527 source lines. Это connected synthetic repo, не production complexity.


| Повтор | A task/protocol | B task/protocol | C task/protocol | C/B wall |
|---|---|---|---|---|
| 1 | BLOCKED/BLOCKED | BLOCKED/BLOCKED | BLOCKED/BLOCKED | null |
| 2 | BLOCKED/BLOCKED | BLOCKED/BLOCKED | BLOCKED/BLOCKED | null |

Медиана wall C/B: null. Uncached-input C/B: null; output C/B: null. Интерпретация: descriptive only; capped/failing runs are not speedup.

Заранее заданный сигнал потенциальной пользы требует обе C task/protocol PASS, качество не хуже B в каждом повторе, median C/B wall ≤0.80 и полные uncached-input/output ratios каждый ≤2.0. Capped/failed runs не считаются ускорением. Два повтора одного synthetic case не дают статистического вывода.

USD и активные человеко-минуты остаются null: actual billing/participation receipts отсутствуют. Наблюдаемые provider counters main/реальных children раскрыты отдельно; неполные totals не дают полного token ratio.

Отдельный общий source/output/report review после batch: BLOCKED. Это не per-run model review и не часть timed task outcome. Предыдущие два раунда сохранены.

Sources, outputs и sanitized receipts: [results.json](results.json), [evidence-index.json](evidence-index.json). Raw provider chats остаются локально.
