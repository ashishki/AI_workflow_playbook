Read `prompts/audit/PROMPT_SIMPLIFY.md` in full and execute it as the
Simplification Reviewer. Use the user's stated scope (file or directory list).
If no scope is given, ask before proceeding — do not silently fall back.

Forbidden:
- writing application code
- modifying tests, source files, or canonical documents
  (`docs/IMPLEMENTATION_CONTRACT.md`, `docs/ARCHITECTURE.md`, `docs/spec.md`,
  `docs/tasks.md`, `docs/CODEX_PROMPT.md`)
- producing a finding that would change behavior
- relaxing any contract rule, security control, or capability-profile rule

Output `docs/audit/SIMPLIFICATION_REPORT.md` from the
`templates/SIMPLIFICATION_REPORT.md` template.

Approved findings become normal Codex tasks added to `docs/tasks.md` only
after the human reads and approves the report. The simplification reviewer
does not implement findings.

This is an opt-in, experimental pass. It does not replace or alter the
mandatory phase-boundary review cycle (META → ARCH → CODE → CONSOLIDATED).
