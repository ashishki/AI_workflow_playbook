# Independent Delivery review — initial

Verdict: CHANGES REQUESTED. Two confirmed P2 correctness issues; no confirmed P0/P1 found in this scope.

Reviewer `/root/delivery_final_review` used a separate platform collaboration session in read-only source scope. This is not a Native Role Runner run. No inference, paid API, credentials, account login, external publication or recursive review was invoked. Temporary project fixtures and review artifacts were the only reviewer writes.

1. Integrated `references/review.md` managed command passes `--root` before `run`; the actual packaged entrypoint rejects that argv (exit 2) before review. Corrected ordering passes offline `--help` (exit 0).
2. Desktop diagnostic rejects foreign-root/missing installation journal as interrupted, but plan/apply ignore those same conditions. A copied project returns `unchanged` on update yet remains interrupted; a missing-journal installation can be removed. No owner-data loss occurred. Unify mutation/diagnostic journal validation.

Observed before fixes: 18 Desktop mechanism tests and 50 vNext tests PASS. Exact reproduction commands, statuses and source identity notes are in `initial.json`; journal fixture outcomes in `initial-journal-reproduction.json`. Root edits started during capture; initial setup_core reproduction therefore uses the exact preserved pre-P2-fix bytes, not a fabricated uniform snapshot. Later test capture is explicitly follow-up source.

Current master Discover/Verify files are preserved (no diff from de2478f). New environment/evidence helpers retain presence-versus-execution, identity-versus-quality and authorization boundaries. Runtime-pointer/final-journal-write regressions pass. Frozen historical evidence was not regenerated.

Limits: Linux technical tests and source audit do not prove clean-machine GUI, Windows/macOS final-source acceptance, real users, field benefit, external preview or completed Cloudflare claim. Final independent recheck is pending final fixes/documentation.
