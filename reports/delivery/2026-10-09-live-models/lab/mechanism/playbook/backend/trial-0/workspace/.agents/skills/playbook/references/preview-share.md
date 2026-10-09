# Preview/share and ownership without DevOps ceremony

Use this only when the user wants to see/share a web result outside localhost or
keep a compatible temporary deployment.

## 1. Instant Share

User language: «Покажи результат», «Открой на телефоне», «Дай временную ссылку».

- Verify the local app/process and exact port first.
- If a Quick Tunnel adapter such as Cloudflare `cloudflared` is available, explain
  that this creates a temporary public URL accessible to anyone who has it.
- Obtain applicable permission before external exposure.
- Never expose sensitive/customer/medical/credential/admin data through an
  unauthenticated quick tunnel by default.
- Verify the live external URL and current app identity.
- Label it temporary preview, not production.
- Stop only the tunnel created by this work when preview is finished.

## 2. Preview → Claim ownership

User language: «Хочу оставить себе», «Сделай это моим», «Хочу сохранить этот
вариант онлайн».

Use only when the solution actually fits a supported claimable deployment model.
For Cloudflare Workers, the agent-native candidate is Wrangler temporary deployment.

Before execution:
- do not log the user out of an existing Cloudflare profile;
- use an isolated config/user context for unauthenticated temporary deployment;
- show Cloudflare Terms of Service and Privacy Policy and obtain explicit acceptance;
- treat the claim URL as a bearer credential and temporary API/token values as secrets.

During execution:
- use the supported temporary deployment command only after permission;
- verify the returned live URL and agreed safe scenario;
- show the claim URL only to the intended owner with its real expiry;
- never put the full claim URL/token in Git, screenshots, shared traces, analytics,
  support notes or normal handoff.

Ownership is complete only when the intended user finishes the provider claim, not
when a URL was generated or opened. After claim, verify the resources remain in the
owner account through a separately authorized path. Do not assume Playbook retains
permanent write access; future deployments need normal owner authorization.

If the claim expires or is not completed, report the temporary deployment as expired,
not lost production. If the architecture/provider is unsuitable, choose another
Introduce path rather than forcing Cloudflare into the solution.

Provider-specific details and acceptance live in repository delivery docs; keep the
user-facing conversation provider-light unless a choice or consent requires detail.
