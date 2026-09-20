# Полный путь рабочего решения

Это способности, не обязательные 13 вызовов или 13 skills. Канонический каталог
включён в пакет: [lifecycle.json](../plugins/playbook-native/skills/playbook/assets/lifecycle.json).

| Этап | Результат |
|---|---|
| [Разобраться](../plugins/playbook-native/skills/playbook/references/lifecycle/discover.md) | Текущий процесс, примеры, участники, исключения и исходная метрика |
| [Выбрать](../plugins/playbook-native/skills/playbook/references/lifecycle/decide.md) | Сравнение ничего/процесс/существующий сервис/шаблон/автоматизация/код/AI |
| [Спроектировать](../plugins/playbook-native/skills/playbook/references/lifecycle/design.md) | Правила, UX, данные, доступы, восстановление и критерии |
| [Создать или настроить](../plugins/playbook-native/skills/playbook/references/lifecycle/build.md) | Законченный результат в рамках запроса |
| [Проверить](../plugins/playbook-native/skills/playbook/references/lifecycle/verify.md) | Настоящий сценарий, сохранность, независимое ревью и ограничения |
| [Встроить в работу](../plugins/playbook-native/skills/playbook/references/lifecycle/introduce.md) | Запуск, владелец, fallback и разрешённые подключения; для web — при необходимости временный безопасный Preview/Share перед production |
| [Наблюдать](../plugins/playbook-native/skills/playbook/references/lifecycle/observe.md) | Эффект на весь процесс без выдуманного выигрыша |
| [Изменить](../plugins/playbook-native/skills/playbook/references/lifecycle/change.md) | Новое правило с сохранением прежнего поведения |
| [Диагностировать](../plugins/playbook-native/skills/playbook/references/lifecycle/diagnose.md) | Причина, затронутые данные и безопасный следующий шаг |
| [Восстановить](../plugins/playbook-native/skills/playbook/references/lifecycle/recover.md) | Восстановление и сверка внешних операций |
| [Передать](../plugins/playbook-native/skills/playbook/references/lifecycle/transfer.md) | Новый человек/сессия продолжает без истории автора |
| [Оценить рост](../plugins/playbook-native/skills/playbook/references/lifecycle/grow.md) | Пользователи, данные, правила, ответственность и проверки |
| [Отключить](../plugins/playbook-native/skills/playbook/references/lifecycle/retire.md) | Экспорт, хранение, отзыв доступа и подтверждённое завершение |

Все процедуры реализованы в библиотеке инструкций. Работа инструментов и
фактическая польза людям имеют отдельную проверку; каталог не утверждает ни
проведённый пилот, ни автоматическое принуждение модели. Engineering-связи —
для автора; ссылки на необязательный Governed не должны требовать его установки
для обычного пользователя. AI-eval guidance входит в Verify и Observe.


## Preview/Share не является новой стадией

Для web-инструмента между **Проверить** и **Встроить в работу** Playbook может
дать владельцу действие «Показать результат»: после локальной проверки и явного
согласия на публичный preview открыть временный HTTPS URL через поддерживаемый
туннель. Пользователь не должен знать команды tunnel/DNS/TLS.

Первый запланированный adapter — Cloudflare Quick Tunnels. Он нужен для быстрого
просмотра на другом устройстве или обратной связи коллеги, а не для production.
URL временный, отдельной аутентификации Quick Tunnel не даёт, поэтому чувствительные
данные и административные поверхности туда не выносятся. Постоянная публикация,
домен и access-control остаются отдельным решением Introduce/Release.


## Preview → Claim ownership

Если web-решение действительно подходит под поддерживаемую Cloudflare Workers
модель, Product может предложить после preview: **«Оставить себе»**.

Это не означает «Playbook хостит ваш продукт». Agent-native маршрут создаёт
temporary deployment, проверяет живой URL и отдаёт intended owner-у приватный
claim URL. После завершённого claim поддерживаемые ресурсы переходят в Cloudflare
account пользователя, а дальнейшие изменения требуют отдельной обычной
авторизации. Claim URL считается bearer credential и не входит в обычный handoff,
Git, screenshots или telemetry.

Capability опциональна и provider-specific. Неподходящее решение не
перепроектируется под Cloudflare только ради красивого onboarding.
