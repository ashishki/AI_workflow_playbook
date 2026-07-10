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
| Exact model ID / revision | | |
| Harness version | | |
| Harness commit / image digest | | |
| Adapter version | | |
| Prompt version | | |
| Tool registry version | | |
| Memory policy | | |
| Permission policy | | |
| Runtime/environment | | |
| Environment digest | | |
| Dataset version | | |
| Sampling manifest | | |
| Scorer version | | |
| Scorer code hash | | |
| Budget | | |
| Trial count | | |
| Invalid-run treatment | | |
| Patch provenance | | |
| Raw EvidenceBundle refs | | |

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
| invalid infrastructure run rate | | | | |
| false-success rate | | | | |
| policy violation rate | | | | |
| evidence correctness | | | | |
| uncertainty / confidence interval | | | | |

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

## Generated Reports

This card is a planning and review artifact. Runtime results must be generated
from raw EvidenceBundles by the harness comparison command, not manually filled
in as proof.

- Baseline bundles:
- Candidate bundles:
- Comparison report:
