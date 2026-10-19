# Источники, версии и границы выводов

Проверено 19 октября 2026. Рекомендации и пороги эксперимента — проектное решение
Playbook, не выводы Relic и не доказательство пользы. Содержимое документации не
равно независимому security audit или тесту исполняемого бинарника.

Публичная страница `https://docs.withrelic.com/guides/importing` не была доступна
через web-fetch при подготовке. Использован официальный репозиторий, не сторонний
пересказ. Для воспроизводимости выбран не `latest`, а **v0.10.2**:
commit `a85219e82110c6321bc7d1b143b6838ebb7190c7` в `heycupola/relic`.
Он подтверждён GET `https://api.github.com/repos/heycupola/relic/git/ref/tags/v0.10.2`.
Это база эксперимента, не утверждение о последнем доступном релизе.

## Что подтверждает документация

- [Importing](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/guides/importing.mdx):
  preview `--dry-run`, конфликты, skip/overwrite; non-TTY способен импортировать новые
  ключи без вопроса; удаление исходника — отдельная опция. Фильтр `scope` по умолчанию
  может быть shared. Импорт не доказывает работоспособность потребителя.
- [Checking keys](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/guides/check.mdx):
  проверка имён без загрузки значений. Статический scan не видит динамические имена
  и может считать обязательными переменные с default. Поэтому в опыте явный template.
- [MCP](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/development/mcp.mdx):
  list-secrets возвращает имена; run-with-secrets маскирует точные значения длиной
  от 4 символов. Авторы прямо называют redaction best effort: encoding/splitting
  может обходить маскировку. Нельзя приписывать CLI run гарантии MCP-вывода.
- [Security](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/configuration/security.mdx):
  клиентское шифрование; потерянный master password не восстанавливается сервисом;
  fallback хранения master password в файл при недоступном keychain. Не обещать
  универсальное отсутствие plaintext на диске VPS.
- [Local development](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/guides/local-development.mdx):
  процессы, запущенные внутри shell, наследуют секреты; фоновые сохраняют их после выхода.
- [Rotation](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/guides/rotation.mdx):
  возраст и политика замены значений, не универсальный перевыпуск у API-провайдеров.
- [Service accounts](https://github.com/heycupola/relic/blob/a85219e82110c6321bc7d1b143b6838ebb7190c7/apps/docs/guides/service-accounts.mdx):
  отдельный проектный machine identity; по данной документации нужен Pro. Данные
  тарифа и доступность проверить перед платными действиями, стоимость неизвестного не ноль.

## Что добавляет наша гипотеза

Одна инженерная запись без значений ключей, разделение разработки и разрешённого
запуска, сохранение правильных прав при переносе, проверка внешнего отзыва и честное
сравнение A/B/C — предлагаемый способ применения. Сам Relic не доказывает уменьшение
времени автора, не защищает любой изменяемый код и не выдаёт разрешения на production.
Синтетический consumer/сканер эксперимента не являются средствами хранения секретов.

## Обновление

Новая версия CLI/agent/хранилища — новая запись версии и новый run root с проверкой
изменившихся команд. Не менять существующий plan/fingerprints и не переносить PASS
со старого бинарника. Подписать нужный источник и hash бинарника перед реальным запуском.
