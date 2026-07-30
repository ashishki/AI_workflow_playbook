# Evidence Index

Status: append-only framework evidence index

| Date | Evidence ID | Scope | Artifact / command | Commit | Result |
|------|-------------|-------|--------------------|--------|--------|
| 2026-07-26 | RAG-EVAL-V2-BASELINE | Pre-change baseline | `docs/IMPLEMENTATION_JOURNAL.md#2026-07-26---rag-evaluation-v2-baseline` | `ee487b2d2c83301933aff8a8b5ecb78050623346` | Baseline recorded; pre-existing Python PATH and frozen toolchain drift noted |
| 2026-07-26 | RAG-EVAL-V2-SCOPED | RAG Evaluation v2 implementation smoke | `docs/IMPLEMENTATION_JOURNAL.md#2026-07-26---rag-evaluation-v2-scoped-verification`; `examples/rag_eval/minimal/comparison.md` | through `5583eca` | Targeted RAG/initializer tests pass; full pytest remained red only for pre-existing frozen Codex/toolchain drift |
| 2026-07-29 | PROGRAM-DESIGN-SLICES | Planning Depth, Feature Design contracts, vertical slice registry, review markers, and changeability mechanism | `reports/implementation/PROGRAM_DESIGN_VERTICAL_SLICES_REPORT.md` | through `c980381` | Contracts, schemas, templates, validators, and docs implemented; synthetic changeability mechanism documented as non-empirical |
| 2026-07-29 | FEATURE-WORKFLOW-END-TO-END | End-to-end Feature Workflow lifecycle from planning facts through slice checks | `reports/implementation/FEATURE_WORKFLOW_END_TO_END_REPORT.md` | through `f237bef` | Thin workflow coordinator, hash-bound approval semantics, review policy, slice lifecycle, initializer integration, and docs implemented |
