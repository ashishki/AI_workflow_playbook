# Receipt Audit Handoff

Date: 2026-10-09. Branch: `feature/receipt-audit`.
Scope: `CHANGE_TASK.md`, extending T04; Lean / lean-core, oneshot.

Implemented `audit_receipt.py` and `tests/test_audit_receipt.py` with Python
standard library only. Run `python3 audit_receipt.py examples/actual-pass/receipt.json`:
observed PASS, exit 0. PASS, FAIL and NOT_RUN are inspection results with CLI
exit 0; INVALID returns exit 2. `command_argv` is returned as data only.
Optional `--strict-exit` returns PASS=0, FAIL=1, NOT_RUN=3, INVALID=2 and
preserves the inspection JSON. It may precede or follow the receipt path.
Only CLI handling changed in the previously reviewed source.

Missing declared stdout/stderr files produce NOT_RUN. Malformed declarations,
unreadable/missing receipt input, invalid JSON, bad hashes, unsafe paths, links,
nonregular files and files over 1 MiB produce INVALID. INVALID takes precedence
over missing evidence. Only stdout/stderr artifacts are required; unrelated
receipt metadata such as `diff_stat_artifact_path` is outside this audit.
Safe nested relative artifact paths are supported. Directory components are
opened without following symlinks; this implementation uses POSIX descriptor
and `O_NOFOLLOW` facilities and was verified on Linux / Python 3.12.13.

Verification actually run:
- `python3 -m unittest discover -s tests -v`: 17 tests, OK (original 13 plus
  four strict-exit checks).
- `python3 audit_receipt.py examples/actual-pass/receipt.json`: PASS.
- SHA256 preservation check: owner notes and all supplied example bytes unchanged
  from this session's baseline. Updated the owner-notes test expectation to the
  authorized SHA256 `e49fd337019931aaeb114e0fd9d2dcc7032391a18380dd8ecf1044a41693ad5f`;
  its foreign handoff line remains. The initial 13-test run had only that known
  stale expectation failure; supplied example hash expectations were unchanged.

T04 remains in_progress until the controller performs the authorized independent
NativeRoleRunner review of the final source and records acceptance. No nested
reviewer or self-review was performed. T01 human/bootstrap acceptance remains
pending; T02/T03 were not reclassified or rerun. Existing evidence and earlier
failure/timeout records were left intact. No external accounts, network calls,
package installation, command replay, or runtime expansion were used.
