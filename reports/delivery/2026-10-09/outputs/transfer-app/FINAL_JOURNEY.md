# Fresh synthetic transfer continuation, 2026-10-09

A separate assistant continued only this transfer-project copy from AGENTS.md,
TASK.md, PROJECT.md, FINAL_JOURNEY.md and the installed Playbook Change/Transfer
routes, with no author chat. Maintainer supplied the new rule: only NEW bookings
may use minute 00 or 30. Legacy HH:MM records, replay ids and backup/restore remain
valid. No stored booking bytes were migrated or changed.

Observed here: 16 unittest checks passed in 9.589s, including legacy 09:15 list/id
reads, same-id replay with changed fields, rejection of new off-grid slots,
whole/half-hour boundaries, isolation/concurrency/persistence/lifecycle regressions,
and actual CLI legacy backup/export/restore on disposable copies. JS syntax check
passed. UI now explains the rule and the existing status output displays the API's
Russian validation error. Browser interaction has not been checked by this assistant.

Actual logs and entry/final hashes: .playbook-artifacts/transfer-20261009/.
TRANSFER_RESULT.md records scope and unchanged data digest. The first failing test
run is retained: historical preservation evidence referenced a generated .pyc absent
from this fresh copy; that old evidence is unchanged, and the fresh entry baseline
now checks the handed-over protected files. A lifecycle test readiness race was
resolved by awaiting HTTP before immediate SIGINT. These are check-tooling changes.

This is synthetic technical transfer evidence only. Root will perform independent
external acceptance after freeze. No nested reviewer, model CLI, external API,
account, publication, field-user return, production auth or full pipeline was run
or inferred here. The preceding author report below remains historical evidence
for its original version, not proof of this changed version.

---

# Synthetic APP journey: implementation handoff

Implemented a working local Russian booking application using Python standard
library only. The two teachers have separate list/id access, header-owned creation,
calendar/time validation, per-teacher slot conflicts and replay-safe request ids.
Thread locking serializes competing operations; atomic JSON replacement persists
records; a process lock prevents maintenance or another server using the same data.

Start from this directory:

```sh
python3 app.py serve --port 8765
```

Open http://127.0.0.1:8765. The server is bound to 127.0.0.1. Default data is
data/bookings.json, created on first start; override via --data PATH. Identity is
explicitly a demo X-Teacher header, not production authentication. Teacher API:
GET/POST /api/bookings, GET /api/bookings/{id}; X-Teacher: anna or boris. POST fields:
student, date YYYY-MM-DD, slot HH:MM, request_id. UI offers both demo identities.

Observed implementation-agent verification:

- Python 3.10.12; `python3 -m unittest -v test_app`: 13 checks passed in 5.536s.
  Raw request/status and test output: .playbook-artifacts/unittest.log.
- Real local HTTP create/list/id access; denied missing/unknown identity; foreign
  id returns the same 404 shape as an absent id; teacher supplied in JSON ignored.
- Twelve competing writes to one slot: one 201, eleven 409; eight concurrent same-id
  writes: one 201, seven 200, one persisted id. Invalid dates/times/JSON return 400.
- Actual separate Python process stopped and restarted with the same data, then
  its persisted booking fetched through HTTP. Running data lock rejected backup.
- Synthetic persistence failure rejected a write with 503 without changing the
  prior persisted bytes. Corrupt restore was rejected without overwriting data.
- Backup/export/restore/retire/resume exercised on temporary copies. A retained
  rehearsal also opened matching exports, restored into a different path, fetched
  the restored record through HTTP, stopped that process, retired that copy, and
  observed serve exit 1 while data remained. Actual command receipts and restored
  API response: .playbook-artifacts/lifecycle-evidence.json. Retained synthetic
  copies: .playbook-artifacts/lifecycle-rehearsal/ (restored.json is intentionally retired).
- Existing notes.txt, TASK.md, AGENTS.md and .agents files matched the saved SHA-256
  baseline (.playbook-artifacts/preserved-baseline.json), checked by unittest.

Current purpose, rules, data/access ownership, costs, commands, restore caveats,
retirement boundary and next-session instructions are in PROJECT.md. No accounts,
paid APIs, global installation, publication, external sends or subscription changes
were performed. The environment has python3; the initial attempt using `python`
failed with command not found and was corrected before verification.

Pending / limits: the implementation agent has not run a real browser or inspected
screenshots. The installed project has no playbook-frontend route. The coordinating
agent will perform real desktop/mobile browser acceptance and independent read-only
review. No nested reviewer was launched. A genuinely separate session continuation
is pending; these handoff instructions alone do not prove transfer. No real human
pilot, adoption, business usefulness or production authentication is inferred.
