# AI Workflow Playbook

**Один Playbook, два способа использования и общие инженерные механизмы.**

| Куда идти | Для чего |
|---|---|
| [Engineering](engineering/README.md) | Рабочая система автора для разработки новых и текущих реальных проектов, глубоких проверок и экспериментов |
| [Product](product/README.md) | Помощь владельцу небольшой рабочей проблемы: разобраться, выбрать изменение, внедрить, наблюдать эффект, изменять и передавать решение |

Это не Pro и урезанный Lite. В Product система организует инженерную работу,
а человек принимает решения о своей работе, данных, расходах и последствиях.
Число skills не ограничивает полноту; небольшой запрос не запускает всю библиотеку.

## Начать

Для Engineering откройте [рабочий маршрут](engineering/USAGE_RU.md): продолжить
проект, начать новый или отдельно проверить новый метод. Действующие проекты
сохраняют закреплённую версию и свой контракт; эксперименты их не обновляют.

Для Product предпочтительный private-preview путь — OS-specific
`Playbook-Desktop`: мастер подключает тот же канонический Native kit к выбранной
рабочей папке, а дальше пользователь работает в Codex обычным разговором.
[Первый запуск](docs/native/QUICKSTART_RU.md).

Native ZIP остаётся переносимым ручным fallback: можно распаковать комплект,
открыть «Мой проект» в Codex и описать проблему без Desktop-мастера.

## Что поставляется

Плагин `playbook-native` сохраняет совместимый путь. В него входят разговорный
вход, frontend, вызываемая библиотека всех 13 этапов, существующий Role Runner
и необязательный инструмент состояния/передачи.

Desktop setup не является новой AI-платформой: он только устанавливает/обновляет/
удаляет управляемые файлы Playbook, умеет вернуть предыдущую **установку** и может
по отдельному подтверждению подготовить per-user runtime для независимого review.
Git, GitHub, VPS, Docker, API key и system Python не являются общими требованиями
для первого Product-разбора.

[Каталог способностей](product/CAPABILITIES.md) ·
[Native kit](distribution/native/README.md) ·
[Desktop setup preview](distribution/desktop/README.md).

**Версия: 0.2.0-preview.3.** Это исходники private evaluation preview, а не
доказанная готовность публичного продукта. Frozen self-test, CI и установка не
подменяют clean-machine, реальный model/browser review, пользовательский пилот и
наблюдение бизнес-эффекта.

Сохраняем [прежние результаты](reports/native/README.md), в том числе опыт,
не установивший преимущество инструкций над обычным Codex. Полный жизненный путь
проверяется отдельно от упаковки.

[Архитектура vNext](docs/vnext/ARCHITECTURE_RU.md) ·
[Общие механизмы](shared/README.md) · [Указатель](docs/README.md) ·
[Desktop delivery status](docs/delivery/DESKTOP_SETUP_PREVIEW_RU.md).

> Репозиторий не получил новую лицензию. Права использования и распространения
> остаются описанными в [LEGAL_STATUS](docs/LEGAL_STATUS.md). Эта ветка не является
> публичным выпуском или разрешением отправлять комплект подписчикам.

> This repository has no project-level open-source license and grants no additional
> copyright permission beyond the GitHub Terms, applicable law, and file-specific
> licenses. See [Legal Status](docs/LEGAL_STATUS.md).

Текущая программа доведения: [D00–D10](docs/delivery/PLAN_RU.md).
