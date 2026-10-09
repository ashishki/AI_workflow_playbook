# Automatic independent review

Use one focused independent review after relevant code changes. The owner does not
need to choose reviewer roles or run terminal commands manually. A failed or denied
review remains explicit; never relabel the main agent's own check as independent.

## Choose the available runner

1. If this project has managed Desktop setup, read
   `.playbook-setup/runtime.json`. It is only a machine-local helper location,
   not execution authority. Use its recorded command with:
   `helper review --root <project> ...`.
2. Otherwise use the bundled Python runner as before when Python 3.10+ and an
   authenticated `codex` CLI are actually available.
3. Do not install Python, Codex, copy credentials, alter the global model or weaken
   permissions merely to turn review green. The Desktop setup may separately
   prepare its pinned per-user review runtime after explicit owner confirmation.

The managed helper embeds the Python needed by the runner; the recipient therefore
does not need a system Python for this path. It may prepend a verified per-user
Codex runtime for the child process. A successful setup or login-status still does
not prove that model execution/review is allowed.

## Execute

Prepare a compact review request under `.playbook-artifacts/` with the original
goal, acceptance criteria, changed paths and observed checks. Keep unrelated chat,
credentials and private records out.

For a managed helper the conceptual command is:

    <local-helper> helper review --root <project> run --profile native --root <project>       --task current-change --role slice_review       --request .playbook-artifacts/review-request.md --timeout-seconds 300

For the manual fallback resolve the script from this installed skill:

    python /path/to/playbook/scripts/run_codex_role.py run --profile native       --root /path/to/project --task current-change --role slice_review       --request .playbook-artifacts/review-request.md --timeout-seconds 300

Use `slice_review` for implementation, `maintainability_review` for a refactor,
`program_design_review` for architecture and `product_design_review` for a
product-design decision. One suitable role is the default, not all four.

Read both status and verdict. Require `status: validated` before crediting the
review. Fix confirmed findings, rerun relevant checks and use at most one focused
follow-up in the ordinary loop. Saved results must be revalidated; source changes
make old evidence stale.

## Limits

The runner owns the fresh read-only Codex child session, timeout, workspace drift
check and tamper-evident local evidence. It does not prove correctness by itself.
Reviewer findings still need judgment.

Do not review text-only answers merely for ceremony. If subprocess/model capability
is absent, say what other checks ran and leave independent review as not run. Package
CI, a CLI `--version` call and account login are not substitutes for a real review.
