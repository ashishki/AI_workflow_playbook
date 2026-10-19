# Подготовка эксперимента — фактические проверки

19 октября 2026. База удалённого master при подготовке:
`84ec63cb516067ec1685a9f13c2f0d7d75a3c8a0`.

## Выполнено локально

- Python 3.13.5, Linux: 23 unit/integration tests этого каталога — PASS.
- `compileall` для новых Python-файлов — PASS.
- Реальный offline CLI: prepare → smoke → scan → report — PASS механизма.
  Искусственные raw/base64/split/file выводы обнаруживаются; отсутствующий,
  неправильный и лишний ключ дают отрицательный результат.
- Сгенерированный отчёт оставил 24/24 живых наблюдения NOT_RUN (trials=1,
  3 условия × 8 cases), оба решения KEEP_EXPERIMENTAL, время/стоимость null.
  Это проверка честного состояния отчёта, не отрицательный результат Relic.
- Первый объединённый локальный shell-прогон превысил внешний timeout инструмента
  после unit tests; его частичные файлы сохранены отдельно. CLI-проход повторён
  в новом каталоге, без перезаписи незавершённого опыта.
- Исходные engineering/USAGE_RU.md и engineering/experiments/README.md восстановлены
  из GitHub fetch и побайтно сверены с Git blob SHA до добавления ссылок.
- Проверка UTF-8 и `git diff --check` для подготовленных файлов — PASS.

В тестах fake provider и намеренно симулированные observation/review записи проверяют
ветви механизма. Их успешный тест НЕ означает успешный live provider/model run.

## Не выполнялось

- Full-repository Native/Desktop/vNext suite: контейнер не смог clone из-за DNS;
  локально были только полученные файлы и новый самостоятельный каталог опыта.
- Реальный Relic, login, import, MCP, ключи и аккаунты: NOT_RUN.
- Реальная модель, A/B/C, независимый Role Runner review: NOT_RUN, CLI недоступен.
- Вторая машина, отзыв настоящего API-ключа и business effect: NOT_RUN.
- Windows/macOS: результаты добавленного CI нужно читать для exact commit отдельно.

Никаких новых результатов эффективности Controlled Delegation/старых пилотов не
создавалось. Product, Desktop, tools/playbook_environment.py и runtime не изменялись.
Ветка готовит исследование, не включает метод и Relic по умолчанию и не выполняет merge.
