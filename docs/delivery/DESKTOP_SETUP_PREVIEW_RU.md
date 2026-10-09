# Desktop setup preview — статус исходников

Source slice: 6 октября 2026. Техническая проверка: 9 октября 2026, preview.4.

Это дополнение к D00–D10, а не новая продуктовая программа. Цель — убрать
технический bootstrap из первого пользовательского прохода, сохранив Codex как
рабочую AI-среду и существующий Product lifecycle как метод.

## Что подготовлено в исходниках

- OS-specific `Playbook-Setup` и консольный `playbook-helper`;
- установка canonical Native kit в выбранную папку без отдельного system Python;
- update/remove только управляемых файлов и отмеченного блока инструкций;
- rollback последней операции установки с явной границей: это не data recovery;
- локальный support-report без project path, токенов и истории чата;
- optional per-user Codex runtime для независимого Role Runner: download только
  после подтверждения, официальный pinned release, SHA256/size verification,
  без global PATH/model/auth edits;
- отдельный owner login;
- frozen offline self-test в Desktop builder;
- Windows/macOS/Linux CI matrix для source tests + Desktop build;
- Native ZIP остаётся manual fallback и единственным canonical payload.

## Что намеренно не считается готовым

- clean-machine запуск на трёх ОС;
- signing/notarization и публичная дистрибуция;
- реальный login/reviewer на каждой ОС;
- реальная browser-проверка из Desktop-пути;
- установка/работа внешних интеграций;
- user pilot, повторное изменение, transfer и бизнес-эффект.

Ни один из этих пунктов нельзя закрыть результатом frozen self-test.

## Проверка владельцем после push

1. Дождаться matrix CI exact commit.
2. Скачать три Desktop artifacts.
3. На чистой Windows/macOS/Linux пройти мастер без dev tools.
4. На каждой ОС подтвердить настоящий reviewer хотя бы на безопасном маленьком diff.
5. Провести один Product-путь: проблема → решение → использование → новая сессия →
   небольшое изменение.
6. Затем только переходить к D09 с преподавателем и 3–5 участниками.

Merge в master остаётся решением владельца после этих прогонов.

## Фактическое дополнение 9 октября

Source `7f36b90` прошёл matrix CI и Linux VPS technical acceptance. Реальные frozen
CLI/GUI lifecycle и extracted START browser выполнены; installation pointer/journal
ошибки исправлены. [Отчёт и SHA ZIP](../../reports/delivery/2026-10-09/REPORT_RU.md),
[точные receipts](../../reports/delivery/2026-10-09/evidence/desktop/acceptance-summary.json).
Windows/macOS CI build/self-test/browser PASS; clean-machine/user/login/reviewer
приёмка там остаётся NOT RUN. Merge private preview source по отдельному разрешению
владельца не закрывает эти gaps и не является решением о выпуске/распространении.
