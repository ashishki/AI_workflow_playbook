# Fresh-session synthetic transfer result — 2026-10-09

Changed only this transfer-project copy. Read the project instructions/current records and installed Playbook Change/Transfer routes without the author chat. One coordinator intervention occurred during the work: a clarification about cache-free copying, preserving the original baseline and first failing logs, and using a separate task-entry baseline. No previous author chat or business-rule/code implementation guidance was supplied; no nested reviewer was used.

New bookings now require minutes 00 or 30. The server checks this after request-id replay and before creation, so valid legacy times remain accepted for stored documents, list/id reads, replay, backup/export and restore. The UI explains the new rule, uses a 30-minute input step, and its existing error status displays the Russian API validation message. No data migration or edit of any current booking bytes.

Observed checks: 16 unittest checks passed in 9.589s; node --check web/app.js exited 0. Actual local HTTP rejects 00:01/09:15/12:45/23:59 for fresh ids and accepts 00:00/00:30/09:00/09:30/23:00/23:30. Every current golden record is readable by its owner, same-id replay returns the exact old record even with another valid off-grid time, and actual CLI backup/export/restore of legacy records succeeds on disposable copies. Existing isolation, conflict, concurrency, persistence, restart and retire/resume checks passed.

Entry/final hashes and logs: `.playbook-artifacts/transfer-20261009/`. `unittest-first-attempt.log` preserves initial failures. Historical `.playbook-artifacts/preserved-baseline.json` is unchanged: it references a generated .pyc absent at task entry in this cache-free copy. The distinct `fresh-transfer-entry-baseline.json` checks current handed-over source files. A test startup race was fixed by awaiting HTTP readiness before immediate SIGINT; application startup code was not changed. `unittest-second-attempt.log` and `unittest.log` preserve the two subsequent passing runs.

Protected AGENTS.md, TASK.md, notes.txt and all 30 present .agents files match entry bytes and file set. Data before/after SHA-256: `b5662024330c52ae8898b083c2419fa69e7acfaca68b71dfedb3ad35ecdce211` (unchanged).

Changed source/current-handoff files and final SHA-256:

- `PROJECT.md`: `650a1cf667ec6dfc68e16c94a10264bfce2652062ea8341b05e99cd4261107fd`
- `FINAL_JOURNEY.md`: `b6049efe4388b395babd2ddfd5e650f9c96ca4529c82474d87035ed03f681395`
- `app.py`: `854adf08dd2f323c6e9a1d07b3a8e5b29e0f9d862ba9efa54fe52399b499c854`
- `test_app.py`: `96543f6b872824423adc77c621372cfc86f3ea5b9c23aca19265de0d1f54c9f6`
- `web/index.html`: `f8873f68057e125758713eb51f7eaf981f74d7985e49014b295bf183fb77946d`


No external API/account/model CLI, publishing, production login, browser interaction or nested reviewer was performed. No field-user return, real pilot, business effect or full delivery pipeline is inferred. Root independent acceptance of this frozen copy remains pending. Current purpose/rules/commands/ownership/checks are updated in PROJECT.md; FINAL_JOURNEY.md separates this continuation from historical author evidence.
