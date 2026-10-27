# Фактическая проверка подготовки

Дата: 27 октября 2026. База:
`2d4a3c421a788f8c4cd015960b686b2f8196c3bb` (удалённый master).
Изменения только Engineering и отдельный CI workflow; Product/Desktop/runtime
и соседние экспериментальные ветки не объединялись.

## Наблюдено локально

- Linux / Python 3.13.5: 21 unittest — PASS.
- Проверены оба layout, совпадение общих тел инструкций, host-specific opt-in,
  выборочная установка, UTF-8 пути, план без записи, сохранение пользовательских
  инструкций, отказ при коллизиях/симлинках/частичной установке и проверка manifest.
- `bundle.py check`, `doctor`, compileall и `git diff --check` — PASS механизма.
- Исходные engineering/README.md и USAGE_RU.md восстановлены из connector и их
  Git blob hashes побайтно совпали с удалёнными оригиналами до добавления ссылок.
- Codex, Claude CLI, agent-browser и heavy отсутствуют в PATH этой среды.
- Playwright/Chromium доступны. Попытка открыть локальный HTTP fixture получила
  `net::ERR_BLOCKED_BY_ADMINISTRATOR`; browser behavior/screenshot acceptance —
  BLOCKED. Политика не ослаблялась, альтернативный обход не предпринимался.

## Не доказано

- Реальное обнаружение/вызов и выполнение в Codex и Claude Code — NOT_RUN.
- Работа agent-browser, полезность замены текущего браузера — NOT_RUN.
- Очередь heavy на VPS, таймауты/сигналы/ресурсный эффект — NOT_RUN.
- Независимый Role Runner review и сопоставление baseline/candidate — NOT_RUN.
- Полный repository suite локально — NOT_RUN: clone через контейнер заблокирован
  отсутствием DNS GitHub; собраны полученные исходники и автономный новый каталог.
- Результаты трёх-ОС CI нужно читать по exact commit отдельно; здесь им PASS
  заранее не присваивается.

Коммит подготовки не является решением о полезности всех четырёх дополнений,
публичным выпуском, поддержкой любого cloud-host или разрешением rollout.
Для дальнейшей приёмки — ACCEPTANCE_RU.md и VPS_PROMPT_RU.md.

## Продолжение приёмки 27 октября 2026

[Новый отчёт и решения по каждому host/addon](../../reports/engineering-addons/2026-10-27-acceptance/REPORT_RU.md)
фиксируют реальные ограниченные Codex и browser пробы, ревью и исправления CI.
Прежние наблюдения выше сохранены как история другой среды; новые наблюдения не
превращают непроверенные Claude, heavy и сравнительную пользу в PASS.
