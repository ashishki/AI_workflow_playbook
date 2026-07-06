# Harness Benchmark Card - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}

## Benchmark Intent

- Decision being tested:
- Baseline harness:
- Candidate harness:
- What must stay constant:
- What is allowed to vary:

## Benchmark Unit

| Area | Baseline | Candidate |
|------|----------|-----------|
| Model/class | | |
| Harness version | | |
| Prompt version | | |
| Tool registry version | | |
| Memory policy | | |
| Permission policy | | |
| Runtime/environment | | |
| Dataset version | | |
| Scorer version | | |
| Budget | | |

## Task Slices

| Slice | Cases | Success metric | Stop condition |
|-------|-------|----------------|----------------|
| happy path | | | |
| ambiguity | | | |
| tool error | | | |
| permission boundary | | | |
| long loop | | | |
| evidence-grounded | | | |
| cost pressure | | | |

## Metrics

| Metric | Baseline | Candidate | Delta | Decision |
|--------|----------|-----------|-------|----------|
| task success rate | | | | |
| unsafe action rate | | | | |
| silent workaround rate | | | | |
| recovery success rate | | | | |
| trace completeness | | | | |
| p95 latency | | | | |
| cost per successful task | | | | |

## Failure Taxonomy

| Failure | Baseline count | Candidate count | Example trace | Owner |
|---------|----------------|-----------------|---------------|-------|
| execution-alignment failure | | | | |
| permission violation | | | | |
| evidence mismatch | | | | |
| tool feedback ignored | | | | |
| non-termination | | | | |

## Decision

Decision: adopt | reject | rerun | needs human review

Rationale:

Follow-up tasks:
