# External Tools / MCP Companion

Status: optional companion guide
Skill descriptor: `templates/skills/external_tools_skill.md`

How to wire any external tool integration — Model Context Protocol (MCP)
servers, REST APIs, gRPC services, or vendor SDKs — into the Tool-Use profile
defined in `PLAYBOOK.md §2c`, without making any specific vendor mandatory.

This is a *worked-example mapping* on top of the existing Tool-Use profile.
It does not introduce a new profile, a new review tier, or a new contract.
The Tool-Use profile already governs side effects, idempotency, unsafe
actions, schema versioning, and side-effect documentation:
`templates/IMPLEMENTATION_CONTRACT.md §Profile Rules: Tool-Use`,
`prompts/audit/PROMPT_2_CODE.md` TOOL-1..6.

---

## When to use this guide

Use it when:

- Tool-Use Profile is `ON` in `docs/ARCHITECTURE.md §Capability Profiles`
- One or more tools is reached through an MCP server (e.g. a vendor MCP
  gateway, a local MCP server you maintain, or a custom one)
- The integration crosses a credential, network, or destructive-action
  boundary

Do not use this guide when:

- The system makes only ordinary application calls that are not LLM-directed
  (Tool-Use Profile = `OFF`)
- The tool is internal application code with no LLM-driven invocation

No vendor is mandated. The terms "MCP" and "MCP server" describe the
integration shape, not a specific provider. Replace any reference to a vendor
with your actual integration.

---

## What this guide is NOT

- not a replacement for the Tool-Use profile rules
- not a substitute for a Tool Catalog row in `docs/ARCHITECTURE.md`
- not a way to skip unsafe-action confirmation tests
- not a path for storing credentials in source

If a tool you are integrating cannot satisfy the requirements below, do not
integrate it under Tool-Use. Either (a) wrap it in a deterministic
application-code path with explicit human gating, or (b) defer the integration
until the requirement gap is closed.

---

## Tool Catalog row — required fields per MCP-backed tool

Every tool reached through MCP must have a row in `docs/ARCHITECTURE.md
§Tool Catalog`. The row contains:

| Field | Purpose | Example |
|-------|---------|---------|
| `name` | LLM-visible tool name | `slack.post_message` |
| `function signature` | Inputs/outputs as the LLM sees them | `(channel: str, text: str) -> {ts: str}` |
| `side-effect class` | `read` / `write` / `destructive` | `write` |
| `idempotency` | `idempotent` / `idempotent-with-key` / `non-idempotent` | `idempotent-with-key` (using `client_msg_id`) |
| `permission required` | What scope/role is needed | `chat:write` on the bot user; bot must be in channel |
| `retry policy` | Allowed retries; backoff; conditions | up to 3 retries on 5xx; never on 4xx |
| `MCP server` | Which server provides the tool, pinned | `internal-slack-mcp@v0.4.2` |
| `unsafe-action gate` | If destructive: confirmation code path | `mode=="confirm" → confirmation payload; mode=="execute" → archive` |

Missing the row is `TOOL-1` (P1 finding). Missing the side-effect class or
idempotency field is `TOOL-1` as well. An unpinned MCP server reference
(`internal-slack-mcp` with no version) is `TOOL-6` (P1).

---

## Side-effect classification

Classify every MCP-backed tool before exposing it to the LLM.

| Class | Meaning | Examples |
|-------|---------|----------|
| `read` | No external state change | `gmail.list_messages`, `github.get_pull_request`, `notion.search` |
| `write` | Creates or modifies external state, reversible without operator action | `slack.post_message`, `github.create_issue`, `notion.append_block` |
| `destructive` | Modifies or deletes state in a way that cannot be undone via the same API, or affects shared state | `slack.archive_channel`, `github.delete_repo`, `gmail.delete_message` |

A tool whose class cannot be determined is treated as `destructive` until
classified. Defaulting to `write` is forbidden — undocumented side effects are
an automatic P1 (`IMPLEMENTATION_CONTRACT.md §Profile Rules: Tool-Use →
Side-Effect Documentation`).

---

## Idempotency

`write` and `destructive` tools must be idempotent where the upstream service
supports it. Concretely:

- prefer APIs that accept an idempotency key
- when no idempotency key exists, document the failure mode in the Tool
  Catalog row and add a `non-idempotent` flag
- never silently retry a non-idempotent destructive call

Tests that exercise an MCP-backed write must include a "called twice with the
same key produces one external effect" case.

---

## Unsafe-action confirmation — code-path requirement

Every `destructive` tool requires an explicit, distinct confirmation branch.
A boolean flag on the request, a comment in the schema, or a string field
named `confirm` is **not** sufficient.

Acceptable shape (illustrative):

```python
def archive_channel(channel_id: str, mode: Literal["confirm", "execute"]):
    if mode == "confirm":
        return present_confirmation_payload(channel_id)
    if mode == "execute":
        return _do_archive(channel_id)
    raise ValueError(...)
```

Unacceptable shape:

```python
def archive_channel(channel_id: str, confirmed: bool = False):
    if not confirmed:
        return {"error": "set confirmed=true"}  # not a code path
    return _do_archive(channel_id)
```

This is enforced by `TOOL-2` (P0 if missing) and the Light Reviewer's
`TOOL-L1` check.

---

## Permission boundaries

Permission must be re-checked at each tool boundary, not only at LLM-call
entry. Single-check-at-entry is `TOOL-4` (P1).

For MCP servers, the boundary is the **server-tool pair**: the same server
exposing both `read` and `destructive` tools must enforce permission per-tool,
not per-server.

When the underlying MCP server uses an OAuth scope or service account, record
the minimum scope/role in the Tool Catalog row. Do not request broader scopes
"for future use".

---

## Audit log requirements

Every MCP tool call emits an audit log entry:

```
{
  ts: ISO-8601,
  trace_id: str,
  actor: <hashed user/session id>,
  tool: <Tool Catalog name>,
  side_effect_class: read|write|destructive,
  idempotency_key: str | null,
  result: ok|error|denied,
  latency_ms: int
}
```

Required regardless of profile combination. Maps to:

- `OBS-1` — external call instrumented in a span with `trace_id` and
  `operation_name`
- `OBS-2` — per-tool labeled counter and latency histogram
- if Compliance Profile = ON: `COMP-2` — security-relevant event audit log

Audit entries must not contain raw PII. Hash any user identifier per
`IMPLEMENTATION_CONTRACT.md §PII Policy`.

---

## Secret handling

- All MCP server credentials come from environment variables. List required
  variables in `docs/ARCHITECTURE.md §Runtime Contract`.
- Never bind-mount credential files into containers (forbidden by
  `IMPLEMENTATION_CONTRACT.md §Docker Security Baseline (T2/T3)` for those
  tiers; treated as P1 if violated regardless).
- Subprocess-launched MCP servers inherit only the variables they need — use
  an explicit allowlist (e.g. `--env-file` with a scoped `.env`), not the
  parent process environment.
- Do not log or trace credential values. Redact at the tracing module
  (`§Shared Tracing Module`).

Credential-mount findings are automatic P1.

---

## Tool-schema versioning

The schema the LLM sees is the contract. Pin it.

- Every MCP server is referenced with a version (`@vMAJOR.MINOR.PATCH` or
  pinned commit hash) in the Tool Catalog row.
- A version bump that changes any tool's schema requires a normal task in
  `docs/tasks.md` tagged `Type: tool:schema` with a test that validates the
  new schema at LLM-generation time, not deferred to executor (`TOOL-3`).
- Provider-side schema changes that arrive without a server version bump must
  trigger a freeze of the affected tools until the change is reviewed.

---

## Rollback policy for destructive tools

Each `destructive` tool documents in the Tool Catalog row:

- whether the upstream API offers a reversal (e.g. `slack.unarchive_channel`)
- the operator runbook for manual reversal when no API exists
- the confirmation mechanism's audit-log entry shape — operators must be able
  to trace "who confirmed what at what timestamp"

A destructive tool with no documented rollback path is a P1.

---

## Worked example — two tools

### Tool A: `slack.search_messages` (read)

```
name             slack.search_messages
signature        (query: str, channel?: str, limit: int = 20) -> {messages: [...]}
side-effect      read
idempotency      n/a (read)
permission       search:read; bot must have access to channel
retry policy     up to 3 retries on 5xx; none on 4xx
MCP server       internal-slack-mcp@v0.4.2
unsafe-action    n/a
```

Tests required:
- schema validation test at generation time (`TOOL-3`)
- `tool_eval.md` row updated when the `tool:schema` task completes (`TOOL-5`)

### Tool B: `slack.archive_channel` (destructive)

```
name             slack.archive_channel
signature        (channel_id: str, mode: "confirm"|"execute") -> {...}
side-effect      destructive
idempotency      idempotent (already-archived returns ok)
permission       channels:manage; admin role on workspace
retry policy     none on 5xx (manual investigation); none on 4xx
MCP server       internal-slack-mcp@v0.4.2
unsafe-action    mode=="confirm" returns confirmation payload;
                 mode=="execute" archives — distinct branches per
                 §Unsafe-action confirmation
rollback         slack.unarchive_channel within 30 days; manual
                 archaeology after that
```

Tests required:
- generation-time schema validation
- two-call confirmation integration test: first call with `mode=confirm`
  returns payload; second call with `mode=execute` archives; `mode=execute`
  without prior confirm in trace context fails closed
- audit log entry assertion for both `confirm` and `execute` modes
- `tool_eval.md` updated with `Eval Source` and `Date`
- `tool:unsafe` task tag → light review fires `TOOL-L1`

---

## How this maps to existing profile checks

| Concern | Existing check | This guide's role |
|---------|----------------|-------------------|
| Tool Catalog completeness | TOOL-1 | Specifies the row schema for MCP-backed tools |
| Unsafe-action gate | TOOL-2, TOOL-L1 | Specifies the code-path shape |
| Schema validation | TOOL-3 | Names the version-pinning convention |
| Permission boundary | TOOL-4 | Reminds that the boundary is server-tool, not server |
| Eval artifact currency | TOOL-5 | Reminds when `tool_eval.md` must update |
| MCP-backed tool integrity | TOOL-6 | New check fired only when Tool-Use=ON; verifies the row matches this guide |
| Observability | OBS-1, OBS-2 | Defines the audit log shape |
| Docker hardening (T2/T3) | §Docker Security Baseline | Reinforces no credential bind-mounts |

---

## Forbidden patterns

- relying on a string field named `confirm` instead of a distinct branch (P0
  by `TOOL-2`)
- granting an MCP server more scope than the listed tools require
- enabling new tools on an existing MCP server without a Tool Catalog row
- treating an MCP server's published tool list as the source of truth — the
  Tool Catalog is canonical; new tools require a `tool:schema` task
- skipping the audit log emission "because the MCP server logs internally"
- mounting `~/.config/<vendor>/credentials` into the container

---

## Reading list

- `PLAYBOOK.md §2c → Profile: Tool-Use` (decision criteria)
- `templates/IMPLEMENTATION_CONTRACT.md §Profile Rules: Tool-Use`
- `prompts/audit/PROMPT_2_CODE.md` TOOL-1..6
- `templates/tasks_schema.md` (tag namespace: `tool:schema`, `tool:unsafe`,
  `tool:call`)
- `templates/skills/external_tools_skill.md` (skill descriptor for this guide)
