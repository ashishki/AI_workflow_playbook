# Sources and design choices

Checked 2026-10-27. These are locally authored, bounded Engineering procedures,
not vendored third-party skill packs. No upstream executable is bundled, no tool
is downloaded by the packager, and no new repository license is granted.
The repository's existing legal status and any upstream tool license still apply.

## Host documentation

- OpenAI, https://learn.chatgpt.com/docs/build-skills
  (redirect from https://developers.openai.com/codex/skills/): repository-local
  `.agents/skills`; `SKILL.md`; optional `agents/openai.yaml` invocation policy.
- Anthropic, https://code.claude.com/docs/en/skills: `.claude/skills`, explicit slash
  invocation and `disable-model-invocation`. This package targets local coding
  sessions, not every cloud/Cowork/desktop mode with different discovery rules.

A documented layout is not a live compatibility result. Host versions and actual
invocation must be recorded at acceptance. Permissions remain host/project policy.

## External inspirations / optional tools

- https://github.com/larchanka/skills/tree/main/project-change-intelligence
  Reviewed SKILL.md in the preceding source review: progressive, evidence-first
  explanation of behavioral/architectural changes. We keep existing records and
  do not require new knowledge directories or parallel agents.
- https://github.com/mattpocock/skills/tree/main/skills/engineering/grill-with-docs
  and https://github.com/mattpocock/skills/tree/main/skills/engineering/tdd
  Inspiration: clarify terms using examples; tests should detect actual mistakes.
  We do not require resolving every future decision, a new glossary/ADR, owner
  approval of every test seam, or a second implementation workflow.
- https://github.com/vercel-labs/agent-browser/blob/main/skills/agent-browser/SKILL.md
  Rechecked blob `dc9bb54a22e9cd7ad9c982a0fe5ae2e204751b12`.
  The current discovery stub points to installed CLI help/skill content. We do not
  adopt its preference over every built-in browser, broad triggers or global install.
- https://github.com/mokevnin/heavy/blob/main/README.md
  Rechecked blob `4217da903120cd4d2a8ae47067611581cdad6c55`.
  Shared local flock slots, nested/CI bypass and child-after-wrapper-death limits.
  This integration does not claim resource/security isolation or Windows support.

Main branch URLs can move. Record exact upstream tool version/digest and host
version before live trials; do not replace that with a skill popularity count.
No independent claim of efficacy is derived from upstream marketing or our packaging.

## Existing Playbook contracts retained

Engineering usage and existing Role Runner remain authoritative. Browser checks
continue to require the right checkout, useful behavior, inspected screenshots and
honest gaps. Product/Native/Desktop runtime is unchanged. These Engineering addons
are explicit optional experiments; full tests/independent review and downstream
adoption remain separate decisions.
