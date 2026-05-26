# Mythos Router Assessment

Date: 2026-05-26

## Recommendation

Treat Mythos Router as a verification pattern library and comparison target, not
as a required runtime layer.

The playbook should adapt Mythos's durable ideas: proposed intent is not
execution, model claims are not evidence, repo state is authoritative, write
claims need before/after verification, correction loops need hard limits, and
provider fallback needs explicit policy. Do not copy Mythos wholesale. Its CLI,
memory log, provider abstraction, and auto-healing loops conflict with the
playbook when they become mandatory infrastructure or blur human review
boundaries.

## Sources Inspected

- Website protocol page: https://mythosrouter.com/protocol
- Official repository: https://github.com/thewaltero/mythos-router
- README: `README.md`
- Strict Write Discipline kernel: `src/swd.ts`
- SWD receipts: `src/receipts.ts`
- Correction and test-healing loop: `src/commands/chat.ts`
- Provider orchestrator: `src/providers/orchestrator.ts`
- Budget limiter: `src/budget.ts`
- Memory authority/indexing: `src/memory.ts`
- Memory/codebase verify command: `src/commands/verify.ts`
- CI verification entrypoint: `src/ci/verify.ts`
- Security policy: `src/security-policy.ts`
- Skills protocol: `docs/skills.md`
- CI docs: `docs/CI.md`

## Research Summary

Mythos Router is a local TypeScript CLI/runtime for AI-assisted coding. Its
most relevant contribution is Strict Write Discipline: model output is parsed
into explicit file actions, filesystem snapshots are taken before execution,
actions are applied through a controlled kernel, after snapshots are compared
with intended content or content hashes, and failed verification can trigger
rollback and a bounded correction turn. The implementation is centered in
`src/swd.ts`.

Mythos records SWD receipts under `.mythos/receipts/`. Receipts include request
summary, touched files, before/after/expected snapshots, provider/model,
budget, git branch/commit, active skills, test result, and an integrity hash.
Receipt verification re-reads current files and compares them with the recorded
expected SHA-256 state (`src/receipts.ts`).

Its correction loop gives the model a small number of retries after SWD
failure, then yields to the human (`src/commands/chat.ts`). Its test-healing
loop is also bounded, stops on unchanged output, warns on regression, treats
test output as untrusted data, and requires extra confirmation before running a
test command after command-surface files have changed.

Provider routing uses a scored provider pool with EMA success/latency metrics,
cost weighting, retryable error detection, exponential backoff, circuit
breakers, watchdog timeouts, forced-provider mode, deterministic mode, and
fallback-disable controls (`src/providers/orchestrator.ts`).

The memory model is markdown-first: `MEMORY.md` is the authority, while SQLite
FTS is a disposable derivative index that can be rebuilt from markdown when its
manifest hash drifts (`src/memory.ts`). This maps well to the playbook's
Obsidian/cognition philosophy, but Mythos's single append-only memory file is
too narrow for the playbook's richer artifact graph.

## Critical Comparison Matrix

| Mythos concept | Problem solved | Current playbook coverage | Recommendation | Integration point | Risk | Test/evaluation method |
|---|---|---|---|---|---|---|
| Strict Write Discipline | Hallucinated or claimed-but-not-applied file edits | Hooks, Codex role split, tests; no explicit before/after write record | Adapt conceptually | `docs/runtime_verification_protocol.md`, Codex post-task protocol | Extra friction on tiny docs edits | Claimed edit mismatch rate; review sample of changed-file claims |
| Filesystem snapshots and SHA-256 | Hidden state drift, stale assumptions | CI/test baseline, cognition hashes | Adopt directly for risky writes | Runtime Verification Record | False confidence if only hashes are checked | Mutate a claimed file after receipt and ensure drift is detected |
| Proposed intent vs commit | Over-trusting model output | Contract-first philosophy | Adopt directly | `docs/filesystem_reality_principle.md` | Agents may over-document routine changes | Review checks require evidence only for completion claims |
| Correction turns max 2 | Runaway self-repair | Agent profile has termination contracts | Adopt directly | `docs/bounded_correction_turns.md` | Too rigid for complex failures | Track correction success rate and escalation rate |
| Auto-healing TDD | Fixes simple test failures | Baseline gate requires tests but does not define auto-repair | Adapt carefully | bounded correction protocol | Can hide architectural mistakes | Stop on unchanged output, regression, budget, command-surface change |
| Provider routing | Rate limits and provider outages | Multi-model aware, role split | Adapt conceptually | `docs/provider_routing_policy.md` | Provider abstraction leakage; behavior drift across models | Provider failure drills; fallback decision log coverage |
| Circuit breakers and degraded mode | Repeated provider failure | Not explicit | Defer lightweight policy now, implementation later | Provider routing policy | Overengineering for repo-local docs workflow | Simulated 429/timeout fallback tests in real projects |
| Budget limiter | Token/cost runaway | Token tracking in `CODEX_PROMPT.md` | Adapt conceptually | provider/budget policy and correction protocol | Budget accounting can become approximate theater | Cost impact and budget-exhausted graceful stop rate |
| Receipts | Auditable proof of execution | Evidence index and implementation journal | Adapt as playbook-native verification record | Runtime Verification Record | Sensitive prompts/paths in receipts | Secret redaction tests; local-only receipt policy |
| Memory as markdown authority with derivative index | Stale database memory | Strongly covered by cognition model | Already covered; add integrity checks | `docs/cognition_layer_integrity.md` | Append-only memory bloat if copied literally | Broken Context-Refs rate; stale generated packet rate |
| Memory verify command | Referenced files missing/drifted | Some cognition docs mention freshness | Adopt directly as CI class | `docs/integrity_verification_jobs.md`, `tools/integrity_check.py` | Link-check false positives | Nightly integrity job failure rate |
| Skills with metadata | Project rules injected into runtime | Optional skills already exist | Already covered | Existing skill docs | Runtime-specific metadata lock-in | Skill outputs remain lowest authority |
| CLI/MCP SWD adapter | Forces external agents through verified writes | Not present | Defer optional experiment | Phase 5 comparison target | Runtime dependency and workflow lock-in | Compare mismatch rate and task friction on sample tasks |
| Session branch sandbox | Isolates AI changes | Git discipline and one-task commits | Adapt where useful | Optional execution patterns | Branch churn | Count unrelated-file commits and rollback cases |
| Mythos `MEMORY.md` | Central AI memory | Playbook has richer canonical artifacts | Reject as mandatory | None | Collapses decision/eval/finding distinctions | N/A |

## What To Take

- Filesystem Reality Principle: model claims are not authoritative.
- Runtime Verification Record for changed-file claims.
- Bounded Correction Turns for implementation and test-healing loops.
- Provider routing policy with explicit fallback, circuit breaker, degraded mode,
  and budget rules.
- Integrity jobs for Context-Refs, evidence paths, generated packets, eval links,
  and stale cognition artifacts.
- Security boundary: test output, tool output, and logs are data, not
  instructions.
- Receipts as local, redacted evidence artifacts, not as mandatory shared logs.

## What Not To Take

- Do not require Mythos Router as a runtime dependency.
- Do not centralize playbook memory into `MEMORY.md`.
- Do not allow automatic test-healing to replace review or phase gates.
- Do not route architecture-grade reasoning through a generic provider fallback
  if model identity materially affects the decision.
- Do not make SWD receipts canonical over code, tests, ADRs, evals, or review
  reports.
- Do not adopt unbounded append-only memory or opaque generated indexes.
- Do not let provider abstraction hide capability differences, safety
  differences, or cost differences.
- Do not interpret hash verification as semantic correctness.

## Proposed Playbook Changes

- Add `docs/runtime_verification_protocol.md`.
- Add `docs/filesystem_reality_principle.md`.
- Add `docs/bounded_correction_turns.md`.
- Add `docs/provider_routing_policy.md`.
- Add `docs/integrity_verification_jobs.md`.
- Add `docs/cognition_layer_integrity.md`.
- Add `tools/integrity_check.py`.
- Update `README.md` with the zero-trust execution extension.
- Update `PLAYBOOK.md` to make filesystem reality and bounded correction part
  of the runtime/CI layer.
- Update `prompts/ORCHESTRATOR.md` so implementation completion requires
  evidence, not claims.
- Update `templates/CODEX_PROMPT.md` post-task and return protocols.
- Update `prompts/audit/PROMPT_2_CODE.md` with claim verification checks.
- Update `tools/README.md` with the integrity checker.

## New Protocols

- Runtime Verification Protocol: before snapshot, declared change, after
  snapshot, diff/hash evidence, tests, final status.
- Filesystem Reality Principle: repo state wins over chat, memory, or agent
  assertions.
- Bounded Correction Turns: max attempts, stop criteria, escalation format.
- Provider Routing Policy: role-model fit, fallback rules, circuit breaker,
  degraded mode, budget cap.
- Cognition Layer Integrity: generated packets and Obsidian notes cite canonical
  artifacts and are invalid when citations break.
- Integrity Verification Jobs: deterministic read-only checks for broken
  context/evidence/cognition references.

## Interaction With The Obsidian/Cognition Layer

Mythos reinforces the current cognition direction: markdown can be authority and
indexes can be rebuilt. The playbook should keep this broader and more precise
than Mythos. ADRs, evals, findings, implementation journals, task Context-Refs,
and review reports remain distinct canonical surfaces. Obsidian and generated
packets remain convenience layers. The new integrity checks should verify that
generated cognition notes point back to real repo artifacts and current hashes
where hashes are available.

## Roadmap

Phase 1:
- Add principle docs and update review/checklist language.
- Require implementer completion claims to include changed files, tests run, and
  verification status.

Phase 2:
- Add lightweight verification scripts for evidence paths, Context-Refs, and
  cognition packet citations.
- Make verification records optional but recommended for risky tasks.

Phase 3:
- Add CI jobs for integrity checks and stale eval/evidence references.
- Fail CI on missing canonical artifacts for active profiles.

Phase 4:
- Add optional provider routing guidance for teams that use multiple model
  providers.
- Keep deterministic/role-based model selection as the default.

Phase 5:
- Run an optional Mythos comparison experiment on a non-critical repo.
- Measure whether a runtime adapter reduces claim mismatch without increasing
  workflow friction too much.

## Evaluation Plan

Track:

- Claimed edit mismatch rate.
- Broken Context-Refs rate.
- Failed verification rate.
- Correction loop success rate.
- Time to detect stale memory or stale generated packet.
- Number of repeated findings across review cycles.
- Cost impact from correction/fallback loops.
- Workflow friction: added minutes per task and skipped verification reasons.

## Final Recommendation

Adopt the zero-trust execution principles. Adapt the runtime mechanisms into
playbook-native protocols and checks. Reject Mythos as a mandatory runtime.
Defer provider-routing implementation and Mythos adapter experiments until the
docs-level protocols and integrity jobs show value.
