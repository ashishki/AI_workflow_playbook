# Test Critic Calibration Protocol

## Status And Purpose

This protocol measures Test Critic and final evidence-auditor behavior against
human-adjudicated known-good changes and seeded defects. No critic is calibrated
merely because this document or a report template exists.

Optimize for bounded, risk-sliced precision and recall, not for more findings or
more blocks. Calibration measures the critic mechanism; project outcome claims
require the paired pilot.

## Authority Boundary

Deterministic failures and missing required evidence block through their
underlying policy whether or not a critic notices them. A critic is advisory
until a current calibration record authorizes a bounded use for the same prompt,
model/build, rubric/taxonomy, task distribution, language, evidence shape, and
risk tier.

| Status | Allowed use |
|--------|-------------|
| `disabled` | Do not use; inputs/output invalid, scope unknown, or evidence unavailable |
| `advisory` | Reviewer signal only; this is the default before thresholds are met |
| `blocking_allowed_low_medium` | May surface a policy stop for the calibrated low/medium scope; deterministic/consolidated/human authority still validates the cited basis |
| `human_confirmed_high_risk` | May recommend a high/critical stop only within calibrated scope; a named human confirms the decision and remains completion authority |

Calibration never permits the critic to waive a deterministic gate, grant
accepted risk, self-approve merge, or treat `NO_FINDING` as proof.

## Dataset Shape

Maintain versioned, project-specific cases. A useful bank contains paired or
closely matched tasks so superficial complexity does not reveal the label:

| Case class | Purpose |
|------------|---------|
| Known-good change | Measures unsupported actionable findings/false alarms |
| Seeded deterministic defect | Measures detection and correct evidence linking |
| Missing required evidence | Tests exact stop-ship basis without a code defect |
| Explicit policy violation | Tests policy citation and authority boundaries |
| Advisory oracle gap | Tests `CONCERN` without severity inflation |
| Approved accepted risk | Tests recognition without critic-granted approval |
| Flaky/invalid run | Tests separation of infrastructure evidence from product failure |
| Multiple-root-cause case | Separate interaction slice for recall and duplicate-finding control |

Stratify by in-scope risk, task type, language/stack, changed boundary, evidence
type, defect family, and diff/context size. High/critical calibration includes
the actual stop-ship categories it may encounter: security/compliance boundaries,
required evidence/holdout failure, baseline weakening, privilege/scope drift,
and approval violations where applicable.

Use one seeded root cause per atomic case in the primary qualification set and
pair it with an independently verified known-good twin where feasible. Keep all
members of a case family in the same dataset split. Multi-defect interactions
belong in their own reported slice; they must not replace atomic cases.

At minimum, report separate slices for deterministic failure, missing required
evidence, explicit stop-ship policy, advisory oracle gap, valid accepted risk,
evidence-complete known-good work, unrelated baseline failure, optional missing
evidence, and stale or mismatched evidence. A project may mark an impossible
slice `not_applicable` before the run with an owner and rationale; it may not
silently omit it after seeing results.

### Case Manifest

Each case records:

- bank ID/version/digest, opaque case ID/version, family/pair ID, dataset split,
  owner, and provenance/license
- risk tier, mode, task/AC, allowed file/diff scope, and context budget
- input artifacts presented to the critic, including deliberately missing items
- ground-truth class: known-good, defect, missing evidence, policy violation,
  accepted risk, or invalid run
- seeded root cause(s), expected Test Critic disposition/basis, expected
  consolidated P/stop-ship severity when applicable, evidence anchors, and
  allowed alternate wording
- human label/adjudication process and disagreement status
- exposure/contamination status, retention, and rotation trigger

Do not expose ground truth, expected findings, or label-bearing filenames to the
critic. Keep a development bank for prompt iteration and a locked calibration
split for authority decisions. A case used to tune the critic leaves the locked
split or is versioned/rotated before the next decision run.

### Bank Layout (Structure Only)

```text
critic_calibration/
  manifest.yaml
  cases/<opaque-case-id>/
    task-and-context/
    diff-or-post-state/
    evidence-manifest.json
  labels-restricted/
    expected-findings.jsonl
  runs/<prompt-model-bank-version>/
  decisions/
```

This repository does not supply seeded project defects. Maintainers create and
review their own cases; scaffolding or invented examples are not evidence.

## Run Protocol

1. Freeze bank/split version, critic prompt and model/build, taxonomy/policy
   versions, tool/environment, context/effort limits, retry policy, and cost
   budget.
2. Register project-specific `N_min(risk, slice)`, `P_min(risk)`,
   `R_min(risk)`, `FA_max(risk)`, and `MISS_max(risk)` before exposing results,
   together with the confidence method and rationale. Every in-scope class must
   have eligible cases; there is no repository-wide universal sample count.
3. Run the critic blind with the same input contract and budget used in the
   intended workflow. Randomize opaque case order where feasible.
4. Validate output structure, cited paths/commands, and authority basis before
   matching findings to labels.
5. Have an independent human/evaluator match findings to seeded root causes and
   adjudicate ambiguous/equivalent claims. Double-label a project-declared
   subset for medium/high use and record disagreement.
6. Compute raw counts, denominators, rates, and uncertainty intervals overall
   and by required slice. Do not let a large easy slice hide a high-risk miss.
7. Inspect false alarms, misses, severity/basis errors, duplicate root causes,
   unsupported citations, and repair outcomes.
8. Record the bounded authority decision, approver, scope, expiry, monitoring,
   and recalibration triggers. Failed runs remain in history.

## Metrics

Match by adjudicated root cause so duplicate prose does not earn extra credit.

| Metric | Definition |
|--------|------------|
| Finding precision | Supported root-cause findings / all actionable findings |
| Defect recall | Seeded in-scope root causes detected / seeded in-scope root causes |
| False-alarm rate | Known-good cases with one or more unsupported actionable findings / known-good cases |
| Miss rate | Seeded-defect cases with an unmatched in-scope root cause / seeded-defect cases |
| Stop-ship recall | Labeled stop-ship targets with a correctly based `BLOCKER` / labeled stop-ship targets |
| Blocker precision | `BLOCKER` findings with a valid observed deterministic/missing-evidence/policy basis / all `BLOCKER` findings |
| Disposition accuracy | Correct `BLOCKER`/`CONCERN`/`ACCEPTED_RISK`/`NO_FINDING` disposition / adjudicated items |
| Severity accuracy | Correct consolidated/final P-level and stop-ship classification / adjudicated severity-bearing findings; report Test Critic disposition separately |
| Evidence-link accuracy | Citations that resolve and directly support the claim/basis / citations checked |
| Repair usefulness | Actionable findings whose bounded proposed verifier/action reproduces, localizes, or leads to a verified fix / actionable findings adjudicated after repair |
| Final false pass | Gold stop-ship cases not stopped by the final authority / gold stop-ship cases |
| Final false block | Gold ready cases stopped without a valid basis / gold ready cases |

Also record output-schema validity, duplicate-finding rate, latency, tokens/cost
when available, retries, and invalid-run rate. Cost/latency are constraints, not
quality substitutes. Report numerator/denominator and slice counts alongside
every rate.

Use one-to-one human-adjudicated matching between critic findings and gold root
causes. Report duplicate and out-of-scope findings separately. A repair counts
as useful only when the target oracle passes, previously green required gates
do not regress, and the repair did not weaken a test or threshold. With no
repair attempt, report `not_measured`; with an empty denominator, report `N/A`,
never zero or 100 percent.

## Threshold Registration And Decision

Create a pre-run table for each intended risk/domain scope:

| Metric/slice | Minimum cases | Required threshold | Rationale/owner | Observed | Decision |
|--------------|---------------|--------------------|-----------------|----------|----------|
| Finding precision | `N_min(risk, slice)` | lower confidence bound >= `P_min(risk)` | | | |
| Defect recall | `N_min(risk, slice)` | lower confidence bound >= `R_min(risk)` | | | |
| False-alarm rate | `N_min(risk, slice)` | upper confidence bound <= `FA_max(risk)` | | | |
| Miss rate | `N_min(risk, slice)` | upper confidence bound <= `MISS_max(risk)` | | | |
| Stop-ship recall | project-declared by in-scope class | project-declared lower confidence bound; any unresolved stop-ship miss prevents promotion | blocking governance floor | | |
| Blocker precision/basis | project-declared | project-declared lower confidence bound; every blocking finding must cite a valid allowed basis | blocking governance floor | | |
| Disposition accuracy | project-declared | project-declared | | | |
| Severity accuracy | project-declared | project-declared for consolidated/final critic scope | | | |
| Evidence-link accuracy | project-declared | project-declared lower confidence bound; unsupported blocker citation prevents promotion | | | |
| Repair usefulness | project-declared | project-declared or report-only during first run | | | |

Thresholds are governance choices, not claims that a sample is statistically
representative. If minimum counts, labels, required slices, or predeclared
thresholds are missing, status stays `advisory`. Do not lower a threshold, remove
a case, relabel a miss, or broaden allowed wording after seeing results without
versioning a new development run.

Promotion uses the preregistered lower confidence bound for higher-is-better
metrics and upper confidence bound for error metrics, not point estimates alone.
The record must retain the interval method and raw numerator/denominator. An
unmet denominator is `advisory`, not a passing result.

Risk-tier decision floor:

| Intended use | Additional requirement |
|--------------|------------------------|
| Optional low-risk review | Advisory; no calibration ceremony required unless a claim/authority is sought |
| Low/medium blocking candidate | All registered thresholds met, zero unresolved stop-ship misses, zero invalid blocker bases, current human approval for exact scope |
| High-risk use | Representative high-risk slices, all low/medium floors, double-label/disagreement record, named human confirmation for every stop decision |
| Critical use | High-risk floor plus named accountable/domain authority; critic remains evidence and never sole transition authority |

## Cadence, Drift, And Monitoring

Calibrate before first blocking use and rerun after:

- critic model/build, prompt, taxonomy, stop-ship policy, tool, or output-schema change
- task/domain/language/evidence distribution or risk-class expansion
- calibration case disclosure/contamination or dataset version change
- a production miss, material false alarm, severity/basis incident, or evidence-link failure
- the project-declared expiry/cadence date

Monitor production Test Critic reports and adjudicate the false-alarm/miss
candidates retained by `templates/TEST_CRITIC_REPORT.md`. A trigger immediately
downgrades authority to `advisory` until recalibration. Never expand authority
automatically from more runs or block rate.

## Anti-Gaming And Claims

- Freeze labels/thresholds before the decision run and keep the locked labels
  outside critic context.
- Balance known-good and defect slices enough to measure both false alarms and
  misses; never reward verbosity or stricter disposition.
- Preserve invalid/failed runs and exclusions with reasons. Exclude invalid
  runs from capability denominators, report their rate, and never let them
  satisfy a gate.
- Use fresh independent adjudication; the implementer/critic cannot label its
  own output as correct.
- Separate mechanism validation from project outcomes.
- Do not optimize block rate, tune on the locked qualification split, selectively
  rerun failures, report only aggregates, or treat critic confidence as quality.
- Quarantine a legitimate novel finding in a known-good case for human audit;
  do not automatically score it as a false positive.

Until a completed calibration report and paired pilot exist, state only that the
protocol and capture fields are available. Do not claim calibrated accuracy,
better repairs, fewer defects, or productivity improvement.

## Related Artifacts

- `prompts/audit/PROMPT_TEST_CRITIC.md`
- `templates/TEST_CRITIC_REPORT.md`
- `docs/merge_authority.md`
- `docs/evaluation/JUDGE_CALIBRATION_PROTOCOL.md`
- `docs/evaluation/PLAYBOOK_EMPIRICAL_VALIDATION.md`
