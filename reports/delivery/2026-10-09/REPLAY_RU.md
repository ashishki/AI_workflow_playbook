# Повторяемость и границы архива

Source runtime закреплён в 7f36b90. Для основного репозитория нужны полный clone
(Git archive anchors D00), dev virtualenv и requirements-dev.txt. Команды pytest,
verify_playbook, vNext, Native и Desktop находятся в основном отчёте/receipts.
Исторические Codex/host probes не становятся доступными от восстановления source.

outputs/initial-app и outputs/transfer-app — точные наблюдённые source snapshots,
включая установленную .agents. Initial содержит один фактически наблюдённый .pyc,
так как старый preservation baseline включает его SHA. Он восстановлен из
сохранённого рабочего каталога с проверкой SHA, не пересобран. Это артефакт
исторического исполнения, не разрешение запускать bytecode или основание доверять
ему. Новый transfer baseline намеренно не включает generated cache; исходный старый
baseline и FAIL на cache-free copy сохранены. Исходники .agents не менялись.

Для повторной проверки snapshot копируйте целиком в одноразовую папку, включая
скрытые .agents/.playbook-artifacts, и запустите там Python 3.10/Linux:
`python3 -B -m unittest -v test_app`. Current corrected snapshot обозначен в REPORT.
Новые app/tests pyc не нужны; bytecode disabled не меняет baseline/source assertions.
Reviewer copies initial/transfer прошли 13/16 checks; основной агент на другой
копии initial получил 1 FAIL из 13 из-за известной startup/SIGINT гонки test helper.
Этот FAIL сохранён, initial suite не объявляется детерминированным. Transfer copy
прошла16checks с ожиданием настоящего HTTP readiness. Это не означает отсутствие
дефектов: финальный reviewer позднее нашёл два других реальных отрицательных случая.

Evidence scripts сохраняют оригинальную VPS layout/paths и рассчитаны на coordinator
сырой experiment directory .playbook-artifacts/delivery-acceptance-20261009/journeys.
Для их replay восстановите соответствующую одноразовую layout: booking-project =
initial-app, transfer-project = transfer-app, corrected-transfer-app = corrected-app;
plan/golden files находятся в evidence/journeys. Output state должен быть новым:
HTTP scripts отказываются повторно использовать созданный output. Browser требует
реальный локальный сервер и pinned Playwright1.61.1/Chromium; используйте наблюдённый
localhost URL аргументом вместо старого динамического порта. Absolute original
paths в raw receipts не переписаны; сохранённые stdout/SHA описывают реальные старые
commands. Эти scripts — scenario probes, не второй Lab или empirical comparison.

ZIP artifacts скачаны/собраны локально и связаны SHA/manifest/CI source head.
Windows/macOS binaries не исполнялись на Linux VPS; их selftest выполнен CI на
соответствующих ОС. Удалённое хранение CI ограничено7днями; постоянный release
не создан. Для новой сборки source/head/OS/freezer/environment нужно фиксировать
снова. PyInstaller hooks и dev зависимости не объявлены полностью pinned;
одинаковые Native bytes не обещают byte-identical OS freezer ZIP.
