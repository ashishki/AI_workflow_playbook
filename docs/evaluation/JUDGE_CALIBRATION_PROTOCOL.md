# Judge Calibration Protocol

## Rule

An LLM judge is advisory until it is calibrated against human labels for the
same rubric, task distribution, language, and risk class. A judge cannot be the
only blocking authority for release, payment, compliance, safety, or destructive
tool decisions without this protocol or a stricter project-specific equivalent.

## Calibration Inputs

| Input | Requirement |
|-------|-------------|
| Rubric | Written criteria with examples of pass, fail, and borderline cases |
| Human sample | Representative cases with at least one human label per item |
| Double-label sample | Subset labeled by two humans when risk is medium or high |
| Judge prompt | Versioned prompt and model identifier |
| Score scale | Categorical labels or numeric scale with threshold mapping |
| Disagreement policy | How human-vs-judge conflicts are reviewed and resolved |
| Recalibration trigger | Model/prompt/rubric change, dataset drift, or scheduled interval |

## Metrics

Choose metrics that match the scoring shape:

| Score type | Primary metric | Secondary checks |
|------------|----------------|------------------|
| Binary/categorical | Cohen's kappa or agreement rate | Confusion matrix, false-pass rate |
| Multi-rater categorical | Fleiss' kappa or Krippendorff's alpha | Per-class disagreement slices |
| Numeric | Spearman/Pearson correlation plus mean absolute error | Threshold crossing accuracy |
| Ranked | Kendall tau or nDCG against human ranking | Top-k disagreement |

High correlation alone is not sufficient. A judge that correlates with humans
but misses stop-ship cases remains advisory.

## Decision Status

| Status | Meaning | Allowed use |
|--------|---------|-------------|
| Disabled | No calibration, weak rubric, or unacceptable false-pass rate | Do not use for gates |
| Advisory | Useful trend signal but insufficient agreement | Reviewer aid only |
| Blocking allowed | Agreement, false-pass rate, and slice analysis meet project threshold | May block low/medium-risk release gates |
| Human-confirmed blocking | Judge flags issues, but human approves final decision | High-risk or regulated release gate |

## Required Report Sections

The project report should include:

- calibration date and owner
- judge model, prompt version, and rubric version
- sample source, size, and stratification
- human label process and inter-annotator agreement when available
- judge-vs-human metrics
- disagreement slices by language, domain, risk, length, and failure type
- cost per judged case
- recommendation: disabled, advisory, blocking allowed, or human-confirmed
- next recalibration trigger

## Stop Conditions

The judge must remain advisory when:

- the rubric is not versioned
- the calibration set is not representative of production cases
- stop-ship false negatives are present and unresolved
- the judge has not been recalibrated after model, prompt, or rubric change
- the project cannot inspect disagreement examples

