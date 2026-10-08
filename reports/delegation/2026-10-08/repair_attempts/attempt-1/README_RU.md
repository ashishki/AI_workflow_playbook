# Неудачная post-hoc попытка исправления

Статус: FAIL. Это frozen evidence попытки, не исправленная production-функция и не повтор A/B/C. Исходные benchmark workspaces не менялись.

Команда: `python3 -m unittest discover -s reports/delegation/2026-10-08/repair_attempts/attempt-1 -v`. Ожидается воспроизведение сохранённых failures; не исключайте расширенные тесты ради PASS. Полный наблюдавшийся вывод — `results.log`.
