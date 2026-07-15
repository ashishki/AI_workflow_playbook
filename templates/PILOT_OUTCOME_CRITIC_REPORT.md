# Blind Pilot Outcome Critic Report

Report ID: {{REPORT_ID}}
Reviewer: {{HUMAN_REVIEWER}}
Pair ID: {{PAIR_ID}}
Task ID: {{TASK_ID}}
Trial: {{TRIAL}}
Blind package SHA-256: {{PACKAGE_SHA256}}
Review status: complete | incomplete

The reviewer used only the blind pair package and did not access the protected
mapping, raw run, prompts, traces, or workflow labels before freezing this
report.

## Candidate Review

| Candidate | Eligible | Rubric results | Oracle concerns | Evidence consistency | Reason |
|-----------|----------|----------------|-----------------|----------------------|--------|
| A | yes / no | pass / fail / unknown per item | deterministic issue / concern / none | consistent / inconsistent / incomplete | {{REASON}} |
| B | yes / no | pass / fail / unknown per item | deterministic issue / concern / none | consistent / inconsistent / incomplete | {{REASON}} |

## Pair Outcome

Outcome: A | B | tie | inconclusive

Material basis: {{RUBRIC_AND_EVIDENCE_BASIS}}

Blinding leak observed: yes | no
Missing or invalid evidence: {{LIST_OR_NONE}}
Residual limits: {{LIST_OR_NONE}}

This report admits or rejects one matched pair for later adjudication. It does
not identify either workflow, authorize adoption, or support an empirical claim
on its own.
