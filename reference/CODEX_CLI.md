# Reference: Codex CLI as Implementation Agent

This document captures hard-won operational knowledge about using `codex exec -s workspace-write`
as the `{{CODEX_COMMAND}}` in the Orchestrator loop. Read this before starting a project that
uses the Codex CLI.

---

## The Golden Rule

**The Orchestrator never writes application code. Codex does.**

This is Rule 1 in ORCHESTRATOR.md and it is absolute. No exceptions for "quick fixes",
"one-liners", or "it's just a comment". If the implementation agent returned `BLOCKED` or
produced a broken result, the correct response is a better prompt — not writing the fix yourself.

Violating this rule silently undermines the entire workflow: the review cycle then covers code
written by the orchestrator (no sandbox, no constraints, no audit trail), and the separation
of concerns that makes the playbook safe collapses.

**If you are tempted to write a fix directly**: stop, write a better codex prompt, re-run.

---

## Invocation Pattern

Always write the prompt to a file first, then pass it via `$(cat ...)`. Never pass prompts
inline via heredoc or string concatenation — long prompts break shell argument limits and
introduce quoting errors.

```bash
# Correct
cat > /tmp/orchestrator_codex_prompt.txt << 'PROMPT'
[your prompt here]
PROMPT
codex exec -s workspace-write "$(cat /tmp/orchestrator_codex_prompt.txt)"

# Wrong — breaks on long prompts, quoting issues
codex exec -s workspace-write "Fix the bug in src/foo.py by doing X..."
```

Use a unique filename per task (e.g. `/tmp/orchestrator_t_r2.txt`) if you are running
multiple tasks or need to debug a failed invocation later.

---

## Known Sandbox Limitations

### Async test suites (aiosqlite, asyncpg, httpx AsyncClient)

**Problem:** `aiosqlite.connect()` and similar async I/O primitives hang indefinitely in the
Codex `workspace-write` sandbox. Codex will report `BLOCKED` or time out on any test that
calls into async DB code.

**Symptom:** smoke_test_db.py hangs, never returns output.

**Workaround:** After every codex run that touches DB-related code, run the test suite
locally to verify:
```bash
.venv/bin/python scripts/smoke_test_db.py
```

Do not treat codex's sandbox test result as authoritative for async test suites. The
orchestrator must always run a local verification step for these.

**What codex CAN verify in the sandbox:**
- `ruff check` / `black` (linters run fine)
- `python -m py_compile` (syntax check)
- Pure stdlib tests with no async I/O
- `import mymodule; print('OK')` style smoke checks

### Heavy model dependencies (Whisper, torch, large ML models)

**Problem:** Tests requiring Whisper, torch, transformers, or other large model loading
will time out or fail in the sandbox.

**Workaround:** Mock these in tests using `unittest.mock.patch`. Do not attempt real
model inference in sandbox-facing tests.

### Package availability

Always tell codex to use the project's `.venv/bin/python`, not the system Python.
Never install packages globally — always into the project venv.

---

## Reading Codex Output

Codex output is often 30–50 KB and gets truncated in Claude Code's display. The full output
is saved to a background task output file. When the result is truncated, read the end of
that file — the important signal is always at the bottom:

- `IMPLEMENTATION_RESULT: DONE | BLOCKED`
- `tokens used: N`
- The final diff hunk (what actually changed)

---

## Prompt Engineering for Codex

### Always specify what NOT to change

Codex is aggressive about "improving" adjacent code. Always add an explicit constraints block:

```
## Constraints
- Do NOT modify any files other than [X, Y]
- Do NOT change LOGGER.* calls
- Do NOT add new imports beyond [Z]
- Run: .venv/bin/python -m ruff check [files]
```

### Reference exact file paths and line numbers

```
# Weak
"Fix the retry logic in the reminders script"

# Strong
"In scripts/send_reminders.py, replace the send_telegram_message function
(currently lines 51–65) with a version that retries on transient failures.
Retry on: ConnectionError, Timeout, HTTP 5xx. Do NOT retry on HTTP 4xx."
```

### For multi-file tasks, describe the change per file explicitly

```
## scripts/send_reminders.py
1. Add `import time` after existing imports
2. Add module constant `TELEGRAM_MAX_RETRIES = 3`
3. Replace send_telegram_message with retry version (signature unchanged)

## scripts/send_summary.py
Apply the EXACT same change as send_reminders.py above.
```

---

## Debugging a BLOCKED Result

1. Read the full output — the blocker reason is in the last 20 lines.
2. Common causes:
   - Missing dependency → add to prompt: "install via `.venv/bin/pip install X`"
   - File not found → verify path in prompt
   - Async test hang → add to prompt: "skip running smoke_test_db.py, only run ruff"
   - Import error → check if import needs a stub/mock in the test environment
3. Write a clean follow-up prompt addressing only the blocker. Do not re-paste the
   original prompt with a note appended — rewrite it.

---

## Checklist Before Running Codex

- [ ] Prompt is in `/tmp/orchestrator_*.txt`, not inline
- [ ] Prompt specifies project root and `.venv` path explicitly
- [ ] Prompt has a Constraints section listing files NOT to touch
- [ ] Prompt ends with `Run: .venv/bin/python -m ruff check ...`
- [ ] If task touches DB/async code: plan to run tests locally after codex returns

---

## After Every Codex Run — Local Verification

Always run the test suite locally. Do not rely solely on codex's sandbox result for
projects using async DB drivers or heavy model dependencies:

```bash
.venv/bin/python -m ruff check src/ scripts/   # lint
.venv/bin/python scripts/smoke_test_db.py       # DB tests (async — must run locally)
```

The local test run is the **authoritative** pass/fail signal, not the sandbox result.

---

## Adding This Reference to ORCHESTRATOR.md

After creating this file, add one line to the "Tool split" table in
`prompts/ORCHESTRATOR.md` under the `{{CODEX_COMMAND}}` note block:

```
<!-- See reference/CODEX_CLI.md for Codex CLI invocation patterns, known sandbox
     limitations (async test hangs, heavy deps), and prompt engineering guidelines. -->
```

Place it directly after the existing CODEX_COMMAND comment block.
