# Judge Calibration Protocol - {{PROJECT_NAME}}

Version: {{VERSION}}
Owner: {{OWNER}}
Date: {{DATE}}
Judge status: disabled | advisory | blocking_allowed | human_confirmed_blocking

## Judge Scope

| Field | Value |
|-------|-------|
| Judge model | {{MODEL}} |
| Judge prompt version | {{PROMPT_VERSION}} |
| Rubric version | {{RUBRIC_VERSION}} |
| Task/domain | {{DOMAIN}} |
| Allowed use | advisory | release gate | reviewer aid | disabled |
| Recalibration trigger | {{TRIGGER}} |

## Rubric

| Label/score | Definition | Example |
|-------------|------------|---------|
| pass | | |
| fail | | |
| borderline | | |

## Human Label Sample

| Sample | Value |
|--------|-------|
| Source | |
| Size | |
| Stratification | |
| Labelers | |
| Double-label subset | |
| Human agreement | |

## Judge Results

| Metric | Value | Threshold | Pass? |
|--------|-------|-----------|-------|
| agreement rate | | | |
| Cohen's kappa / alpha | | | |
| false-pass rate | | | |
| false-fail rate | | | |
| stop-ship false negatives | | 0 | |
| cost per judged case | | | |

## Disagreement Slices

| Slice | Count | Pattern | Action |
|-------|-------|---------|--------|
| language | | | |
| domain | | | |
| long input | | | |
| high risk | | | |
| ambiguous | | | |

## Decision

Decision: disabled | advisory | blocking_allowed | human_confirmed_blocking

Rationale:

Next recalibration date or trigger:
