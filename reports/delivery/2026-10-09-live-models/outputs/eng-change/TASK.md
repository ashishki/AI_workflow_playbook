# ENG-NEW: a real maintainer evidence utility

The Playbook maintainer needs a small usable tool to inspect saved command receipts instead of reading large JSON logs. Build audit_receipt.py using Python standard library only. Command: python3 audit_receipt.py /path/to/receipt.json; outputs one JSON object with status PASS/FAIL/NOT_RUN/INVALID, reason, exit_code and command_argv as data. CLI exit0 for PASS/FAIL/NOT_RUN inspection; exit2 for INVALID input.

Contract supplied by owner/maintainer:
- schema_version must be playbook.command_receipt.v1; receipt must be a JSON object, exit_code integer excluding bool, timed_out in environment_summary boolean.
- Verify stdout/stderr files against their declared SHA256 before saying PASS or FAIL. Missing evidence means NOT_RUN, mismatched evidence means INVALID. A timeout means FAIL when evidence is intact. Nonzero exit means FAIL. Successful exit with intact evidence means PASS.
- Only bounded regular receipt and artifact files (max1MiB each) in the receipt directory. Reject absolute/../artifact escapes and symbolic/hard links. Do not fetch URLs, run command_argv, modify evidence, install packages, publish, or use accounts.
- Preserve owner-notes.txt and supplied real example files byte-for-byte; add meaningful tests and concise current project/handoff notes with actual commands/constraints.
- This is a real new maintainer tool on copied real public receipts; not a human productpilot. Root controller performs independent separate read-only review through authorized OpenCode; no nested reviewer processes.
