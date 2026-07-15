# Test-First Pilot Approval

Approval ID: `<3-64 lowercase path-safe characters>`
Pilot ID: `<3-64 lowercase path-safe characters>`
Manifest SHA-256: `<sha256 of ASSET_MANIFEST.sha256>`
Critic report SHA-256: `<sha256 of CRITIC_REVIEW.md>`
Approver: Artem Shishkin
TFA-7.1: approved
TFA-7.2A: approved
TFA-7.2B: approved
TFA-7.2C: approved
Repository: `ashishki/shishki_bot`
Fixture bases: `59ff47bdbcfb32fb1f128fcf6ac37f6fa0bd8c26`; `5f9adb4f7421c7cc03e74c8dd30c127f3ecfd31d`
Sparse fixture boundary: approved
External permission profile and verifier sandbox: approved
Scorers, ledger, schedule, and missing-value rules: approved
Local evidence boundary: trusted single-writer host; no concurrent mutation; no independent attestation
Codex executions: 12
Internal inference calls: not bounded
Paid API budget: USD 0
Retries: 0
Retention: raw 90 days; sanitized 365 days
Decision: approved

The durable approval record must replace every angle-bracket placeholder and
retain the exact machine-checked lines above. One approval ID and pilot ID may
authorize only one attempted schedule. Every attempted Codex execution counts
against the twelve-execution ceiling; the runner never retries an invalid or
quota-failed attempt.
