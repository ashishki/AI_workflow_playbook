# UI Verification Protocol

## Purpose And Boundary

UI acceptance needs separate evidence for behavior and appearance. This protocol
defines a project-owned evidence contract; it adds no UI, browser runtime,
snapshot service, CI job, or required Playbook dependency.

Playwright screenshot assertions, Percy, and Chromatic are examples of tools a
project may select. The Playbook requires the routed evidence properties, not a
specific vendor or framework.

## Three Independent Layers

| Layer | Proves | Does not prove |
|-------|--------|----------------|
| Behavior checks | Interactions, navigation, state transitions, validation, accessibility-relevant semantics, and error handling | Layout, clipping, overlap, typography, color, or fidelity |
| Deterministic visual comparison | Baseline/current/diff for declared states and viewports under a stable capture environment | That interactions work or that a new/changed baseline is acceptable |
| Visual review | A human assesses new/changed baselines and hard-to-formalize fidelity; an optional vision critic may supply advisory observations | Deterministic behavior, merge authority, or empirical superiority |

No layer substitutes for another when both behavior and visual acceptance are in
scope. A screenshot is not a behavior test; a DOM assertion is not layout proof;
a vision-language verdict is not a deterministic diff or human approval.

## Routing

Resolve `Risk-Level`, `Public-Tests-Required`, and `Visual-Contract` before
implementation. Public-test routing controls behavior specs. Visual routing
controls screenshot/diff/review evidence.

| Resolved visual contract | Treatment |
|--------------------------|-----------|
| `not_applicable` | Rendered appearance is not an acceptance surface. Record the reason and use routed behavior tests/verifier; create no placeholder screenshots. |
| `optional` | Visual evidence may add signal but is advisory. Its absence/failure does not become stop-ship unless the task is reclassified. |
| `required` | Declared visual state/viewport evidence, stable capture metadata, diff artifacts, console evidence, and required human review/authority gate completion. |

High/critical user-facing UI changes resolve visual evidence to `required`.
`optional` or `not_applicable` is valid at those tiers only when the change is
non-UI/behavior-only and the rationale shows appearance is not affected. A
conflict produces `TEST_GOVERNANCE_GAP`; do not silently downgrade.

### Risk And Mode Minimums

| Route / risk | Minimum evidence |
|--------------|------------------|
| Optional, any risk where allowed | Routed behavior evidence; any screenshot/diff is advisory and explicitly labeled optional |
| Required low/medium | Routed behavior checks for changed semantics; AC-complete states and smallest supported viewport set; baseline/current/diff or reviewed initial baseline; console artifact; human review of every new/changed baseline |
| Required high | Low/medium evidence for every affected state/viewport, independent human visual review, exact evidence map, and high-risk task approval |
| Required critical | High evidence plus applicable negative/error/failure states, pre-execution approval, post-evidence human approval, and stop-ship for missing/stale/unexplained evidence |

Lean-Core uses the smallest state/viewport set that proves the acceptance
criteria. Standard maintains stable baselines for affected UI boundaries. Strict
adds durable retention and independent review but does not create a visual gate
for non-UI work. Risk strengthens the task-local floor without escalating every
other task.

## Visual Contract

Before capture, record:

- task/AC and component/page/flow boundary
- named UI states, including applicable loading, empty, validation, error,
  permission-denied, and long-content states
- supported viewport IDs with width, height, device-scale factor, and the real
  product breakpoint each represents
- browser/engine and version, OS/runtime when material, locale, timezone, color
  scheme, reduced-motion setting, font assets/version, and fixture/data version
- readiness condition used before capture, such as fonts loaded, network idle,
  animation settled, or explicit component signal
- project-owned diff method and predeclared threshold/rationale
- baseline owner, storage/retention/access policy, and required reviewer

Do not add arbitrary desktop/mobile screenshots unrelated to supported
breakpoints. The matrix should be stable and acceptance-driven, not viewport
theater.

## Stabilization And Dynamic Content

Prefer deterministic fixtures, fixed clocks, seeded data, stable network mocks,
loaded local fonts, disabled transitions, and explicit wait conditions. Record
every stabilization action.

Mask, hide, or restyle only a truly nondeterministic region that is not part of
acceptance. For each treatment record target, method, reason, and reviewer. Never
mask an area changed by the task, an error/permission state, primary content, or
any region whose layout/fidelity is being accepted. Broad masks and blanket
threshold increases are evidence weakening.

Capture browser console errors, unhandled rejections, failed resources, and
relevant accessibility/runtime warnings as a separate artifact. Define the
project policy, such as no new errors relative to baseline; do not infer it from
the screenshot.

## Baseline Lifecycle

An initial baseline is a review candidate, not a self-validating pass. A new or
changed baseline record includes:

- task/AC and reason for the update
- exact state/viewport paths affected
- prior baseline, current capture, and diff where a prior baseline exists
- capture-environment and stabilization changes
- threshold/mask/config changes
- human reviewer, decision, timestamp, and follow-up/accepted risk

Blind regeneration or bulk acceptance without inspecting affected diffs is
forbidden. Changing a viewport, browser, font, locale, threshold, mask, fixture,
or capture readiness condition is a baseline-policy change and receives the
same review as image changes. Unexplained baseline deletion is missing evidence.

## Evidence Record

| Evidence | Required content when routed |
|----------|------------------------------|
| Behavior | Exact command/result/receipt for changed interactions and states |
| Capture environment | Browser/version, locale/timezone/theme, fonts, fixture, readiness signal, and tool/config version |
| Viewport coverage | Stable ID, dimensions, device-scale factor, supported breakpoint rationale |
| Screenshots | State + viewport + baseline/current artifact references |
| Visual diffs | Diff artifact, observed delta/metric, predeclared threshold/rationale; no self-assigned readiness verdict |
| Stabilization | Fixed data/time/animation/network treatment plus every targeted mask/style and reason |
| Console | Console/network/runtime artifact and disposition of new errors/rejections |
| Baseline update | Task rationale, changed matrix/config, prior/current/diff, human review reference |
| Authority | Resolved route/risk, human review/approval reference, and missing evidence |

Screenshots may contain credentials, personal data, customer content, or internal
URLs. Use deterministic non-sensitive fixtures, redact exports, and apply the
project's access/retention policy. Do not solve leakage by masking an
acceptance-critical area.

## Failure Handling

| Observation | Treatment for required evidence |
|-------------|---------------------------------|
| Behavior check fails | Fix behavior through public test-first loop; visual green cannot override it |
| Unexplained visual diff exceeds the predeclared rule | Review and fix, or explicitly approve the intended baseline change |
| Evidence is missing/stale or matrix/config changed silently | Stop-ship as missing required evidence; recapture and review |
| Capture is invalid/flaky due environment or dynamic content | Repair stabilization/runner; do not update baseline to hide noise |
| New console/resource errors exist | Triage under project policy; record fix or approved disposition |
| Optional evidence is absent/different | Advisory only; reclassify first if appearance is actually acceptance-critical |

## Human And Vision Review

Human visual review is required for every new/changed required baseline and for
high/critical UI readiness. The reviewer sees the acceptance criteria,
baseline/current/diff, state/viewport matrix, capture changes, masks, and console
evidence.

A vision critic may be used after behavior and deterministic visual evidence for
complex layout/fidelity observations. It is advisory unless a future calibrated
policy explicitly grants bounded authority. It cannot replace human review,
grant accepted risk, or turn model confidence into stop-ship. Cross-vendor use
is optional.

## Claims Boundary

This protocol defines evidence collection and review. It does not prove fewer UI
defects, improved fidelity, faster review, or better outcomes. Such claims
require recorded pilot evidence.

## Related Protocols

- `docs/testing/test_first_protocol.md`
- `docs/runtime_verification_protocol.md`
- `docs/merge_authority.md`
- `templates/RUNTIME_VERIFICATION_RECORD.md`
