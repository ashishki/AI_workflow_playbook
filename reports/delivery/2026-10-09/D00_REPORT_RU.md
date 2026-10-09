# D00: восстановление достоверной основы

Дата наблюдений: 9 октября 2026. База: `de2478f4a3fdffb4c568898f37a078500f203b8a`.
Изменения выполнены отдельно от master. Это исправление dev/CI и проверяющих
инструментов, а не новый исторический pilot или включение делегирования.

## Что изменилось и зачем

Harness Lab устанавливается из действующего локального пакета вместе с dev
dependencies. Чистый Python 3.12 virtualenv действительно создан, зависимости
установлены; импорт и `pip check` выполнены. Pytest больше не пропускает целые
модули из-за отсутствия исторической среды: переносимые контрактные проверки
работают, недоступные host-проверки перечисляются отдельно. Опция
`--strict-environment-pilots` превращает отсутствие предпосылки в ошибку сбора.
Неуспех CLI identity probe также остаётся ошибкой.

Замороженный manifest относится к старым исходникам, поэтому проверять его на
изменяемом современном дереве неверно. Новый archive verifier проверяет точный
снимок из локальной Git-истории по внешнему SHA256 и затем запускает проверенный
исторический builder. CI загружает полную историю. Текущий старый live-builder
по-прежнему отвергает drift; frozen manifest, toolchain, registry, runner,
permissions verifier и suite не переписаны.

Сохранённый manifest содержит 179 файлов и соответствует
`965612aa463fca1a35a55104633d0e09da33d615`. Июльский опубликованный pilot ссылается
на другой, исходный manifest из 119 файлов, `d00575aa4fe599e7a72acfb732aa5fb16ffc4df4`.
Эти проверки подтверждают целостность исходников, а не исполнение или approval.

Шесть сломанных ссылок TFA-7 заменены ссылками на честную
[запись доступности](../../../docs/evaluation/TEST_FIRST_PILOT_EVIDENCE_AVAILABILITY.md).
Четыре исходных локатора сохранены как NOT AVAILABLE. Исторические выводы и их
байты сохранены; отсутствующие execution/review/approval артефакты не придуманы.

Реальные проверки sandbox выявили две дополнительные проблемы: Bubblewrap 0.6.1
не поддерживал обязательный `--disable-userns`, а symlink Python из virtualenv
указывал на недоступный alias. На VPS собран Bubblewrap 0.9.0 из
[официального релиза](https://github.com/containers/bubblewrap/releases/tag/v0.9.0),
SHA256 исходного tar проверен: `c6347eaced49ac0141996f46bba3b089e5e6ea4408bc1c43bab9f2d05dd094e1`.
Sandbox поддерживает выбранный virtualenv и только aliases доверенного Python;
доступ к домашним каталогам не расширен, защитный флаг сохранён.
Это новая техническая среда, не восстановленный исторический pinned host.

## Фактические результаты

| Проверка | Статус | Наблюдение |
|---|---|---|
| Первоначальный полный pytest | FAIL | 2 failed, 256 passed, 12 skipped; исходный результат сохранён |
| Pytest после исправлений, до установки поддерживаемого sandbox | PASS с NOT RUN | 292 passed, 6 skipped; явные ограничения окружения |
| Полный pytest на подготовленном VPS | PASS с NOT RUN | 296 passed, 2 skipped, 13 subtests passed |
| Общий `verify_playbook.py` | PASS | required_failures=0, реальные initializer/negative fixtures выполнены |
| Реальная Bubblewrap изоляция | PASS | read-only workspace, недоступность host secrets, сеть, дочерние процессы, exit code |
| Historical pinned CLI 0.144.4 probe | NOT RUN | установлен CLI 0.160.1; подмена identity не выполнена |
| Historical pinned host match | NOT RUN | исторические пути отсутствуют; новые бинарники не имеют старых hashes |
| Strict historical collection | FAIL ожидаемо | rc4 при отсутствующей pinned предпосылке; проверка не обходится |
| Июльский pilot approval/run/review | NOT RUN | первичные локальные артефакты отсутствуют |

Команды, exit codes, timestamps, полные stdout/stderr и SHA256 сохранены в
[evidence/d00](evidence/d00/). Два запуска полного suite и canonical выполнялись
параллельно на одном VPS; это проверки корректности, не измерение быстродействия.
Receipts фиксируют базовый commit и dirty tree; точные изменённые исходники
связаны через [source SHA256](evidence/d00/source-sha256.json).

Независимый read-only reviewer обнаружил ещё два P2: абсолютный запуск Python
и virtualenv `--copies`. Исправления подтвердил отдельным повторным запуском:
43 PASS / 1 historical-host SKIP; altered Python copy отвергнут до verifier.
[Начальные замечания](evidence/d00/review-initial.json) сохранены отдельно от
[повторного PASS](evidence/d00/review-recheck.json). Это collaboration agent,
не Native Role Runner. Native package: 24 PASS без root, без permission skip.
CI учитывается отдельно в общем отчёте после фактического завершения. Стоимость inference для этих команд — ноль вызовов;
стоимость работы основной сессии/агентов и время человека здесь не измерены.

## Ограничения

296 успешных тестов не закрывают real Product-пилоты, внешние accounts, публичный
Preview/Claim или решение о выпуске. Root VPS не подтверждает Unix chmod защиту
для обычного пользователя; отдельные переносимые package-проверки запускаются
без root. Исторические live gates остаются обязательными для нового исполнения
того pilot и не заменяются успешной проверкой source archive.
