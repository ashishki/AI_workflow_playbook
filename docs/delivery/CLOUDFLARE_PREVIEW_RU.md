# Cloudflare Quick Tunnels: бесшовный Preview/Share

Дата проверки источников: 20 сентября 2026.

## Задача

Нетехнический владелец не должен разбираться в localhost, DNS, сертификатах и
туннелях только ради того, чтобы увидеть сделанный web-инструмент на телефоне или
показать его коллеге.

Пользовательское действие: **«Показать результат»**.

Внутренний первый adapter: Cloudflare Quick Tunnels (`try.cloudflare.com`).

## Почему подходит

Cloudflare описывает Quick Tunnels как временный публичный доступ к локальному
web-сервису через `cloudflared tunnel --url http://localhost:<port>`.
Для Quick Tunnels не требуется Cloudflare login; Cloudflare выдаёт HTTPS URL,
а пользователю не нужно настраивать DNS или сертификат.

Официальные источники:
- https://try.cloudflare.com/
- https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/do-more-with-tunnels/trycloudflare/
- https://developers.cloudflare.com/sandbox/concepts/preview-urls/
- https://developers.cloudflare.com/changelog/post/2026-07-14-temporary-accounts-api/

## Граница

Quick Tunnel — **preview**, не production deployment и не proof of ownership.

По текущей документации generated URL не управляется пользователем и отдельной
аутентификации Quick Tunnel не предоставляет. Поэтому случайный адрес — не
security boundary.

Не использовать по умолчанию для:
- production/customer data;
- medical/financial/private records;
- credentials/secrets;
- admin/debug surfaces;
- действий, которые сами изменяют production.

## UX-контракт

Пользователь говорит: «Покажи результат».

Playbook:
1. находит только свой/явно выбранный web-process;
2. проверяет локальный адрес и текущую версию;
3. если `cloudflared` отсутствует — объясняет один setup gap, ничего скрытно не
   устанавливает;
4. если данные/экран безопасны для публичного preview — объясняет одной фразой,
   что временная ссылка будет публична для любого, кто её получил;
5. после согласия запускает tunnel;
6. получает фактический URL из процесса, не угадывает его;
7. проверяет удалённый URL через браузер/HTTP и основной безопасный сценарий;
8. отдаёт человеку ссылку с меткой «временный preview»;
9. по окончании останавливает только tunnel, созданный этой сессией.

Если доступ должен быть ограничен определёнными людьми, Quick Tunnel без
дополнительного access-control не подходит.

## Что измерить на VPS и с пользователем

Технически:
- Linux/VPS: фактический tunnel start/URL/remote request/stop;
- wrong port / dead local app / tunnel failure;
- отсутствие `cloudflared`;
- локальная и внешняя версия совпадают;
- tunnel не остаётся скрыто запущенным;
- URL не сохраняется как production endpoint.

С пользователем:
- смог ли он попросить «покажи» без технических терминов;
- сколько дополнительных объяснений потребовалось;
- открыл ли URL на другом устройстве;
- понял ли различие preview и опубликованного приложения;
- не пришлось ли ему пользоваться Cloudflare dashboard/CLI самостоятельно.

## Дальнейший вариант

Cloudflare Temporary Accounts API (июль 2026) позволяет платформам создавать
временный Worker/account до входа пользователя и затем выдавать claim URL.
Это потенциально ещё ближе к бесшовному «создать → показать → забрать себе»,
но требует уже продуктовой интеграции, принятия Cloudflare Terms/Privacy,
proof-of-work, API lifecycle и отдельной проверки лимитов/ownership. Пока это
research candidate после подтверждения ценности простого Preview/Share.
