# Cloudflare: бесшовный Preview/Share и Preview → Claim

Дата проверки источников: 20 сентября 2026.

## Задача

Нетехнический владелец не должен разбираться в localhost, DNS, сертификатах и
туннелях только ради того, чтобы увидеть сделанный web-инструмент на телефоне или
показать его коллеге.

Пользовательское действие: **«Показать результат»**.

Внутри два разных adapter-path:

1. **Instant Share** — Cloudflare Quick Tunnels (`try.cloudflare.com`) для
   безопасного временного показа локального web-процесса.
2. **Preview → Claim** — Cloudflare Temporary Accounts для совместимых Workers:
   live deployment создаётся до входа пользователя, затем владелец получает
   claim URL и забирает поддерживаемые ресурсы в свой Cloudflare account.

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

## Preview → Claim ownership

Это planned Product capability, а не только research note.

Cloudflare поддерживает два уровня интеграции:

- **Wrangler `deploy --temporary`** — для агента/CLI. Wrangler управляет
  proof-of-work, temporary credentials и выводит live URL + claim URL.
- **REST Temporary Accounts API** — для собственного platform backend, если он
  появится позже. Backend получает temporary account ID/API token и claim URL.

Для текущего Playbook приоритет — Wrangler path: он проще и не требует строить
собственный backend.

По текущей документации:
- unauthenticated Wrangler flow поддерживается с 4.102.0+;
- claim нужно завершить в течение 60 минут; просто открыть URL недостаточно;
- если claim не завершён, temporary account/resources удаляются;
- после claim supported resources остаются в account пользователя;
- claim не даёт платформе permanent access — будущий deploy требует обычной auth;
- claim URL — bearer credential, temporary API token — secret;
- эти значения нельзя помещать в client-side code, shared telemetry/logs;
- supported resources ограничены Workers/workers.dev, Static Assets, KV, D1,
  Durable Objects, Hyperdrive, Queues и частью certificate operations с лимитами.

Ключевой продуктовый принцип: **Playbook помогает создать и передать владение,
но не остаётся скрытым хозяином инфраструктуры**.

## UX-контракт Preview → Claim

Пользователь: «Хочу оставить себе».

Playbook:
1. объясняет возможность временно развернуть и затем забрать ресурс;
2. проверяет совместимость, не перестраивая неподходящее решение ради провайдера;
3. не разлогинивает существующий Cloudflare profile;
4. показывает Terms/Privacy и получает явное согласие;
5. создаёт temporary deployment в изолированном context;
6. проверяет live URL;
7. показывает claim URL только владельцу и срок истечения;
8. после completed claim подтверждает переход ресурсов владельцу;
9. не сохраняет temporary secrets;
10. для последующих изменений использует обычный owner-authorized deployment path.

VPS acceptance находится в `VPS_ACCEPTANCE_RU.md`, раздел B3.