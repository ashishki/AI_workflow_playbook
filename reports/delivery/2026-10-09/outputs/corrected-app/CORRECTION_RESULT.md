# Corrected synthetic transfer prototype, 2026-10-09

This is a NEW corrected copy of transfer-project. Frozen old prototypes, reports,
results, instructions and legacy data have not been rewritten. The inherited
FINAL_JOURNEY.md and TRANSFER_RESULT.md remain historical records of their versions.
No new human pilot, account, model CLI, browser session or nested reviewer ran here.

Two independently reported P2 findings were reproduced against the old transfer
app before editing this copy. The first RED regression run observed 14 assertion
failures across 7 methods. It includes a real os.replace followed by a one-shot
actual directory-fsync fault: the disk commit was erased by the next different
request on the old Store. CLI metadata output collisions were also reproduced.
The first RED log is retained unchanged.

Changes in app.py:

- Any Exception from a Store write discards the in-memory document, reloads and
  validates the actual disk under the request lock, and returns 503 describing
  an uncertain outcome plus retry with the same request_id. A committed rename
  therefore remains visible to replay and subsequent different requests.
- If reload is unavailable or invalid, the Store remains unavailable and has no
  stale cache. list, id reads and creation all return 503 without writing until
  explicit recovery/reopening. Stop the server, inspect or restore the selected
  JSON while offline, then restart and retry the same request_id. No automatic
  blind write, cache fallback or fabricated rollback occurs.
- export, backup and retire reject output paths reserved for the retirement
  marker, process lock and restore checkpoints before creating/opening the lock
  or changing files. Resolved marker/lock symlink targets are also reserved.

Observed final checks: `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest -v test_app test_corrections`
passed all 24 methods in 12.985s (16 inherited, 8 new regression methods). New
cases verify the real post-rename fsync fault, exact replay id, immediate different
request preserving both commits, actual precommit rename failure, unavailable and
invalid disk reload failing closed, recovery/reopening, and real CLI byte-preserving
refusals for metadata/checkpoint paths, existing markers and dangling symlinks.
An earlier full 23-method GREEN and focused 7-method GREEN are retained too; the
24-method log is the result for the final app hash below.

Evidence in .playbook-artifacts/correction-20261009/:

- RED-old-transfer.log — first regression run targeting the old app with bytecode
  disabled; old source and evidence stayed untouched.
- GREEN-corrections.log, GREEN-full.log, GREEN-full-final.log — actual observed
  outputs. The final complete run is GREEN-full-final.log.
- old-transfer-baseline.json — complete pre-correction SHA-256 map of the frozen
  transfer directory; exact post-work equality was verified, including old logs.
- correction-hashes.json — old/new source hashes and protected copied file hashes.

Old transfer app.py SHA-256: `854adf08dd2f323c6e9a1d07b3a8e5b29e0f9d862ba9efa54fe52399b499c854`
Corrected app.py SHA-256: `82d0417f3fab4923e82e768bf5121ba60dfc2f6c4519195544bf7e8bcf291788`

Run from this corrected directory: `python3 app.py serve --port 8765`.
localhost only: http://127.0.0.1:8765. Existing synthetic data/bookings.json was
copied byte-for-byte, including legacy off-grid appointments; new bookings still
require minutes 00 or 30. X-Teacher remains demo identity, not production auth.
For acceptance, select a separate --data PATH rather than altering legacy data.

This corrected copy is frozen for coordinating-agent acceptance and recheck by
its existing independent reviewer. Neither new local verification nor inherited
old outcomes substitute for that reviewer result or a real usefulness pilot.
