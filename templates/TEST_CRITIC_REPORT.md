# Test Critic Report - {{PROJECT_NAME}}

Report ID: {{REPORT_ID}}
Task: {{TASK_ID}} - {{TASK_TITLE}}
Run ID: {{RUN_ID}}
Date: {{DATE}}
Report status: complete | incomplete
Critic result: NO_FINDING | ADVISORY | STOP_SHIP

## Purpose And Authority

This report records an independent audit of task oracles and evidence. It does
not approve task completion, phase advance, or merge. A blocking finding is
valid only when it cites a deterministic failure, missing resolved-required
evidence, or an explicit stop-ship policy.

Create a report only when `Critic-Required` resolves to `required` or a human
requests a scoped optional audit. A low-risk Lean task whose route resolves to
`not_required` does not need a report. Store each completed run at a unique
durable path such as docs/audit/TEST_CRITIC_<TASK_ID>_<RUN_ID>.md; do not
overwrite prior runs needed for later calibration.

## Run Context

| Field | Value |
|-------|-------|
| Critic identity/session | {{CRITIC_IDENTITY}} |
| Critic model/build | {{MODEL_OR_BUILD_ID}} |
| Prompt source/version | `prompts/audit/PROMPT_TEST_CRITIC.md` @ {{PROMPT_VERSION}} |
| Adoption mode | Lean-Core / Standard / Strict |
| Risk-Level | low / medium / high / critical |
| Critic-Required | declared -> resolved |
| Trigger | required / conditional:predicate / optional human request |
| Diff scope | {{BASE_HEAD_OR_CHANGED_FILES}} |
| Human completion authority | {{OWNER_OR_POLICY_REF}} |

### Calibration Run Metadata (when applicable)

Keep expected labels hidden during the critic run. A human/evaluator fills the
adjudication fields only after the report is finalized.

| Field | Value |
|-------|-------|
| Calibration bank ID/version/digest | {{BANK_ID_VERSION_DIGEST_OR_NA}} |
| Split | development / locked qualification / n/a |
| Opaque case ID/version | {{CASE_ID_VERSION_OR_NA}} |
| Pair/family ID | {{PAIR_FAMILY_ID_OR_NA}} |
| Rubric version | {{RUBRIC_VERSION_OR_NA}} |
| Taxonomy / policy version | {{TAXONOMY_POLICY_VERSION_OR_NA}} |
| Tool/environment version | {{ENVIRONMENT_VERSION_OR_NA}} |
| Context/effort/retry budget | {{RUN_BUDGET_OR_NA}} |
| Input-bundle digest | {{INPUT_BUNDLE_DIGEST_OR_NA}} |
| Prompt digest | {{PROMPT_DIGEST_OR_NA}} |
| Trial index | {{TRIAL_INDEX_OR_NA}} |
| Critic output hash | {{OUTPUT_HASH_OR_NA}} |
| Calibration record / authority status | {{CALIBRATION_AUTHORITY_REF_OR_ADVISORY}} |

## Input Manifest

| Input | Expected reference | Observed status | Notes |
|-------|--------------------|-----------------|-------|
| Canonical task and acceptance criteria | {{TASK_RECORD_REF}} | present / missing / stale | |
| Resolved governance route | {{ROUTE_REF}} | present / missing / conflict | |
| Public RED/GREEN evidence | {{PUBLIC_TEST_REF_OR_NA}} | present / failed / missing / n/a | |
| Broader verification | {{BROADER_CHECK_REF}} | present / failed / missing | |
| Diff/repository state | {{DIFF_REF}} | present / missing / mismatch | |
| Runtime/command receipts | {{RECEIPT_REFS_OR_NA}} | present / failed / missing / n/a | |
| Holdout result summary | {{HOLDOUT_RESULT_REF_OR_NA}} | present / failed / missing / n/a | Never include restricted cases |
| Mutation/property evidence | {{STRONGER_ORACLE_REFS_OR_NA}} | present / failed / missing / n/a | |
| Visual evidence | {{VISUAL_REF_OR_NA}} | present / failed / missing / n/a | |
| Exception/approval records | {{APPROVAL_REFS_OR_NA}} | present / missing / n/a | |

Missing required inputs: {{MISSING_INPUTS_OR_NONE}}

## Routing Snapshot

| Gate | Declared -> resolved | Expected evidence | Evidence reference | Observed status |
|------|----------------------|-------------------|--------------------|-----------------|
| Public tests | {{VALUE}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | sufficient / weak / failed / missing / n/a |
| Test Critic | {{VALUE}} | this report | {{REPORT_ID}} | complete / incomplete |
| Holdout | {{VALUE}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | sufficient / failed / missing / n/a |
| Mutation | {{VALUE}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | sufficient / weak / failed / missing / n/a |
| Property | {{VALUE}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | sufficient / weak / failed / missing / n/a |
| Visual contract | {{VALUE}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | sufficient / weak / failed / missing / n/a |
| Human approval | {{RISK_TIER_FLOOR}} | {{EXPECTED_OR_NA}} | {{REF_OR_NA}} | recorded / missing / n/a |

## Acceptance-Criteria Evidence Map

| AC | Expected behavior | Public test evidence | Holdout result | Receipt / other evidence | Coverage | Gap ID |
|----|-------------------|----------------------|----------------|--------------------------|----------|--------|
| AC-N | {{BEHAVIOR}} | {{COMMAND_RESULT_OR_NA}} | {{RESULT_REF_OR_NA}} | {{REF_OR_NA}} | covered / partial / missing / not_applicable | TC-GAP-N / none |

Coverage here means traceable oracle coverage of the named acceptance criterion;
it is not a line-coverage percentage or a correctness claim.

## Oracle Audit

| Check | Applicable scope | Evidence | Disposition | Finding / gap |
|-------|------------------|----------|-------------|---------------|
| Boundary, negative, and failure cases | {{SCOPE_OR_NA}} | {{REF_OR_NA}} | sufficient / weak / missing / n/a | {{ID_OR_NONE}} |
| Sensitivity to absent/wrong fix | {{SCOPE}} | {{REF}} | sufficient / weak / missing | {{ID_OR_NONE}} |
| Public-fixture hardcoding or overfitting | {{SCOPE}} | {{REF}} | none observed / concern | {{ID_OR_NONE}} |
| Flaky or non-reproducible signals | {{SCOPE}} | {{REF}} | none observed / concern | {{ID_OR_NONE}} |
| Evidence traceability and freshness | {{SCOPE}} | {{REF}} | sufficient / weak / missing | {{ID_OR_NONE}} |
| Public/holdout independence | {{SCOPE_OR_NA}} | result metadata only | sufficient / concern / n/a | {{ID_OR_NONE}} |

## Findings

Counts: BLOCKER={{N}} CONCERN={{N}} ACCEPTED_RISK={{N}}

### TC-N - BLOCKER | CONCERN | ACCEPTED_RISK - {{TITLE}}

- Category: oracle_gap | missing_case | public_test_overfit | flaky_signal | evidence_traceability | route_conflict | accepted_exception
- AC / Gate: {{AC_AND_GATE}}
- Claim: {{FALSIFIABLE_CLAIM}}
- Evidence: {{PATH_LINE_COMMAND_RESULT_OR_MISSING_ARTIFACT}}
- Deterministic result or policy citation: {{REQUIRED_FOR_BLOCKER_OR_NONE}}
- Stop-ship basis: deterministic_failure | missing_required_evidence | explicit_stop_ship | none
- Impact: {{BOUNDED_IMPACT}}
- Required next action: {{NARROW_ACTION}}
- Confidence: high | medium | low
- Calibration mapping: blinded during run; {{MATCH_ID_OR_PENDING}} after adjudication

For `ACCEPTED_RISK`, record the existing exception below. Without a complete
human-approved record, classify the item as `CONCERN`, not accepted risk.

| Owner | Reason | Scope | Compensating evidence | Expiry / follow-up | Approval reference |
|-------|--------|-------|-----------------------|--------------------|--------------------|
| {{OWNER}} | {{REASON}} | {{SCOPE}} | {{REF}} | {{DATE_OR_TASK}} | {{HUMAN_APPROVAL_REF}} |

When no findings exist, omit finding blocks and record:

- NO_FINDING scope: {{ACS_GATES_COMMANDS_AND_ARTIFACTS_CHECKED}}
- Residual limits: {{OPTIONAL_UNAVAILABLE_EVIDENCE_OR_NONE}}

## Unresolved Oracle Gaps

| Gap ID | AC | Missing oracle/case | Risk | Proposed deterministic check | Owner | Disposition |
|--------|----|---------------------|------|------------------------------|-------|-------------|
| TC-GAP-N | AC-N | {{GAP}} | low / medium / high / critical | {{CHECK}} | {{OWNER}} | blocker / concern / accepted risk |

## Calibration Candidates

These are raw candidates for later human/evaluator adjudication. They are not
confirmed critic metrics and do not support an empirical improvement claim.

### False-Alarm Candidates

| Candidate | Related finding | Reason | Evidence | Adjudicator/date | Status |
|-----------|-----------------|--------|----------|------------------|--------|
| TC-FA-N | TC-N | {{WHY_POSSIBLY_FALSE}} | {{REF}} | {{HUMAN_OR_PENDING}} | candidate / confirmed / rejected |

### Miss Candidates

| Candidate | Seed / issue / later finding | Why critic may have missed it | Evidence | Adjudicator/date | Status |
|-----------|------------------------------|-------------------------------|----------|------------------|--------|
| TC-MISS-N | {{REF}} | {{REASON}} | {{REF}} | {{HUMAN_OR_PENDING}} | candidate / confirmed / rejected |

### Post-Run Calibration Adjudication

_Fill after the critic output is frozen. Do not expose this section to the critic
during a blind calibration run._

| Field | Human/evaluator annotation |
|-------|----------------------------|
| Ground-truth class | known_good / seeded_defect / missing_evidence / policy_violation / accepted_risk / invalid_run |
| Adjudicator(s), date, disagreement | {{HUMAN_RECORD}} |

Match findings to gold items one-to-one. Do not count duplicate prose as another
true positive.

| Critic finding ID | Gold root-cause ID | Match | Predicted / gold disposition | Predicted / final P severity | Evidence links supported | Repair attempted / outcome | Evidence |
|-------------------|--------------------|-------|------------------------------|------------------------------|--------------------------|----------------------------|----------|
| TC-N | GOLD-N / none | TP / FP / duplicate / out_of_scope | {{VALUES_OR_NA}} | {{VALUES_OR_NA}} | yes / no / n/a | yes / no; useful / not_useful / not_measured | {{REF}} |

Record every unmatched gold item; these are the source of false-negative and
miss metrics.

| Unmatched gold ID | Expected disposition / severity | Miss basis | Evidence | Adjudicator |
|-------------------|---------------------------------|------------|----------|-------------|
| GOLD-N | {{VALUES}} | {{WHY_UNMATCHED}} | {{REF}} | {{HUMAN_DATE}} |

Repair usefulness requires the target oracle to pass, no regression in
previously green required gates, and no weakened test or threshold.

## Handoff

- Stop-ship bases observed: {{TC_IDS_OR_NONE}}
- Advisory concerns: {{TC_IDS_OR_NONE}}
- Accepted risks: {{TC_IDS_OR_NONE}}
- Missing required inputs: {{LIST_OR_NONE}}
- Next owner/action: {{OWNER_AND_ACTION}}
- Consolidated/human authority reference: {{POLICY_OR_REVIEW_REF}}

The consolidated review and applicable human policy layer decide disposition.
This report alone cannot close a finding or authorize completion.
