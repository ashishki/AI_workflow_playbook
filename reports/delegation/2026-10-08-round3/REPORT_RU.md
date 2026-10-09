# Что показал третий раунд

Проведены **6/6 настоящих A/B/C-прогонов** на связанном синтетическом проекте: 67 файлов, 44 исходника, 527 строк рабочего кода. В каждом запуске исправлены три причины сбоя в inventory, checkout и refunds. Все шесть получили **100/100 / application PASS**; первое независимое ревью подтвердило правильность кода и объяснений всех шести результатов.

Добавочная польза делегирования **не показана**. В обоих повторах C медленнее B. Медиана C/B времени — **1.46×**; uncached input — **2.93×**, output — **1.69×**. Это наблюдаемые расходы и длительность завершённых приложений с одинаковой оценкой, не квалифицированное сравнение полностью проверенных workflows: scope инструкций workers неизвестен.

**Application PASS; protocol A/C BLOCKED, B PASS; полная qualification BLOCKED. Решение: не включать делегирование по умолчанию.**

| Повтор | A, с | B, с | C, с | C/B время |
|---|---:|---:|---:|---:|
| 1 | 259.085 | 229.588 | 380.293 | 1.66× |
| 2 | 240.119 | 254.914 | 327.763 | 1.29× |

| Режим | Median, с | Input | Cached input | Uncached input | Output | Workers |
|---|---:|---:|---:|---:|---:|---:|
| A | 249.602 | 1487599 | 1302272 | 185327 | 22480 | 3 в каждом |
| B | 242.251 | 579462 | 503040 | 76422 | 16494 | 0 в каждом |
| C | 354.028 | 1900100 | 1676160 | 223940 | 27827 | 3 в каждом |

Counters полные во всех шести попытках: отдельные persistent provider threads main и 12 настоящих native workers. CLI main summary не прибавляется повторно. Время включает работу модели и её проверки; operator scoring и послеэкспериментальное ревью раскрыты отдельно. **USD и активные человеко-минуты неизвестны / NOT MEASURED**, не ноль и не ценовая оценка.

Критерий был закреплён до calls: одинаково успешные B/C, median C/B ≤0.80, полные uncached-input/output ratios ≤2.0. Наблюдённые время и uncached input не достигают порогов даже без проблемы проверки scope. Два повтора одного среднего synthetic repo не дают статистического или production-вывода и не проверяют automatic routing.

## Исправление оценщика и независимое ревью

Первый настоящий общий read-only Native review: **validated STOP_SHIP**. Он обнаружил, что поиск literal markers в opaque `gAAAAAB…` сообщениях породил четыре необоснованных protocol FAIL. В отдельной posthoc-интерпретации они заменены на **BLOCKED**, не PASS. Оригинальные receipts, scores, источник `0c27438`, четыре FAIL и исходный STOP_SHIP сохранены. Новых model runs или task repairs после batch не было. [Коррекция](evidence/posthoc-protocol.json), [первое ревью](review/initial-report.md).

Дополнительно найдены actual child custom-tool calls/stdout трёх CLI replay-команд из STATE A2. Это связанные исходные журналы, а не повторная имитация исполнения. [Свидетельство](evidence/a2-child-commands.json).

Будущий collector различает unreadable/unknown и подтверждённое нарушение, не скрывая реальные deadline/inheritance defects. Будущий prompt ясно разрешает A solo work. В этом batch общий текст подталкивал A к workers: A/C действительно использовали по три. Поэтому A не считается чистым solo или unprompted baseline; основной ориентир — B.

Повторная независимая проверка исправлений и скорректированной интерпретации: **validated / PASS**. Её scope и фактические counters указаны в results.json. Первое полное ревью и повторная проверка не входят в task ratios. Координаторские и подготовительные model tokens здесь не измерены.

Прогоны выполнены под root после явного разрешения владельца, одной моделью gpt-6.1-sol/high, последовательно, без repair, per-run model reviewers, внешних аккаунтов и production действий. Source/parent/child evidence локально в `.playbook-artifacts/delegation-round3/runs`; raw chats не публикуются. Inherited worker sandbox не доказывает отдельную OS read-only изоляцию.

[results.json](results.json), [evidence-index.json](evidence-index.json). Предыдущие раунды и preflight сохранены.

Source checks после исправлений: **111 vnext PASS**, contracts PASS, runtime sync PASS. [Receipts](source-validation.json).
