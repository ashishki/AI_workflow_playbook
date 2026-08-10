# Audited Rounds Demo V1

Status: mechanism demonstration, not empirical evidence.

Script:

1. Round 1 Executor claims success.
2. Round 1 Auditor rejects because required receipt/evidence is insufficient.
3. Audited state keeps `REQ-1` open.
4. Round 2 Executor fixes the issue and supplies a receipt.
5. Round 2 Auditor verifies the receipt.
6. Deterministic `apply-audit` marks `REQ-1` verified and completes the run.

This fixture demonstrates state advancement only after verified audit evidence.
It does not claim real-model quality improvement.
