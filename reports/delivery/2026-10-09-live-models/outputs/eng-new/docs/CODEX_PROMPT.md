# Receipt Audit Handoff

Date: 2026-10-09. Branch: `feature/receipt-audit`.
Scope: T04 in `TASK.md` and `docs/tasks.md`; Lean / lean-core, oneshot.

Implemented `audit_receipt.py` and `tests/test_audit_receipt.py` with Python
standard library only. Run `python3 audit_receipt.py examples/actual-pass/receipt.json`:
observed PASS, exit 0. PASS, FAIL and NOT_RUN are inspection results with CLI
exit 0; INVALID returns exit 2. `command_argv` is returned as data only.

Missing declared stdout/stderr files produce NOT_RUN. Malformed declarations,
unreadable/missing receipt input, invalid JSON, bad hashes, unsafe paths, links,
nonregular files and files over 1 MiB produce INVALID. INVALID takes precedence
over missing evidence. Only stdout/stderr artifacts are required; unrelated
receipt metadata such as `diff_stat_artifact_path` is outside this audit.
Safe nested relative artifact paths are supported. Directory components are
opened without following symlinks; this implementation uses POSIX descriptor
and `O_NOFOLLOW` facilities and was verified on Linux / Python 3.12.13.

Verification actually run:
- `python3 -m unittest discover -s tests -v`: 13 tests, OK.
- `python3 audit_receipt.py examples/actual-pass/receipt.json`: PASS.
- `sha256sum owner-notes.txt examples/actual-pass/*`: original hashes preserved;
  the test suite also checks the four supplied files against their original hashes.

T04 remains in_progress until the controller performs the authorized independent
read-only OpenCode review of the final source and records acceptance. No nested
reviewer or self-review was performed. T01 human/bootstrap acceptance remains
pending; T02/T03 were not reclassified or rerun. Existing evidence and earlier
failure/timeout records were left intact. No external accounts, network calls,
package installation, command replay, or runtime expansion were used.
