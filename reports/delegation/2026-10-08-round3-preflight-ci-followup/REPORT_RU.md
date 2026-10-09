# Исправление переносимости тестов после подготовки третьего раунда

Native Product Checks для `01af29e7eb305a98679c9f5430aa03925bc438a5`
дал FAIL в macOS job; vNext, Linux/Windows package checks и desktop jobs прошли.
[Исходный CI](https://github.com/ashishki/AI_workflow_playbook/actions/runs/37820910748).

Два новых теста зависели от среды. Тест reviewer snapshot использовал временный
путь через системный alias `/var`, хотя snapshot generator сохраняет canonical
paths. Тест process timeout запускал `/usr/bin/python3` вместо интерпретатора
тестовой среды; до deadline macOS не успевал получить начальное событие процесса.

Исправлены только тестовые fixtures: временный root нормализуется через resolve,
а локальный тестовый процесс использует sys.executable. Проверки сохранены:
hash binding, покрытие всех шести outputs, настоящий timeout и partial receipt.
Source приложения, модельный task, веса, бюджеты и исходные данные не менялись.

После исправления 108 локальных тестов PASS. macOS повторно проверяется CI
следующего коммита; локальный Linux PASS не назван доказательством macOS PASS.
Свидетельства исходного FAIL и фактического локального повторения —
[evidence-index.json](evidence-index.json).

Замороженная подготовка `2026-10-08-round3-preflight` не переписывалась.
Её pending-plan закрепляет старый source/test fingerprint; для реального запуска
после решения вопроса среды нужен новый каталог с актуальной версией исходников.
Все модельные A/B/C-прогоны третьего раунда по-прежнему NOT RUN; итоговое
независимое ревью NOT RUN. USD и активное время человека неизвестны.
