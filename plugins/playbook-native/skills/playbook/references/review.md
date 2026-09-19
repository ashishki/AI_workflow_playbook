# Automatic independent review

The existing Playbook Role Runner is included under `scripts/`. Use it by
default before presenting completed code changes: automatic and quick modes
include one focused read-only review after the relevant implementation checks.
The user does not need to choose a reviewer, install the old governed framework,
or ask for review separately. Their explicit scope and project policy still apply.

For check-only work, use the same runner for an independent assessment when
writing temporary evidence is permitted. Plan-only stops before implementation
and does not create review artifacts. Text-only answers do not need a code review.
If `PLAYBOOK_REVIEW_WORKER=1` or the current assignment already identifies you as
the independent reviewer, complete your assigned review without spawning another.

## Execute

1. Check that Python 3.10+ and the authenticated `codex` CLI are available to this
   session. Do not change the user's global model, permissions or authentication.
   If capability is missing/denied, explain the missing review and the next step;
   never label your own check an independent review or silently downgrade PASS.
2. Write a short request under `.playbook-artifacts/` with the original user goal,
   acceptance criteria, changed paths and observed checks. Supply facts, not the
   verdict you want. Include relevant project constraints. No task registry or
   Feature Design files are needed. Keep unrelated conversation/history out.
3. Run the bundled helper, resolving its path from this skill's actual location:

   ```text
   python /path/to/playbook/scripts/run_codex_role.py run --profile native --root /path/to/project --task current-change --role slice_review --request .playbook-artifacts/review-request.md --timeout-seconds 300
   ```

   Use the available Python command (`python3`, `python`, or `py -3` on Windows).
   Choose `slice_review` for implementation; `maintainability_review` for a refactor;
   `program_design_review` for an architecture decision; `product_design_review`
   for a product-design decision. One appropriate role is the default, not all four.
   Model and reasoning inherit host configuration unless project policy explicitly
   requires particular values. A new project needs no Git setup for native review.
4. Read the returned JSON and report. A completed command alone is not acceptance:
   require `status: validated`, inspect findings and limitations, and act on them.
   Fix confirmed problems within the task, run relevant checks again, then perform
   one focused follow-up review if the first review found blockers. At most two
   reviewer attempts in the ordinary loop; remaining blockers go in the final answer.
   A failed/denied reviewer is an incomplete review, not a reason to relax access.

Before relying on a saved result, run the same helper's `verify --root ... --result ...`.
Keep the runner's files under `.playbook-artifacts/runs/`, including failed attempts.
Do not delete or move them to tidy the diff or satisfy quick mode; they are the
measurement and failure record. Do not retry an access denial through a different
filesystem route, copied authentication or weaker permissions.
Native verification checks the captured project files as well as artifact hashes;
an older report becomes stale when reviewed source changes. Keep reviewer execution
sequential with edits. Report independent review and remaining findings in plain
language; the user need not inspect the ledger or internal marker names.

## Delivery and limits

This is the same engine as `tools/run_codex_role.py` and `tools/codex_role_run_lib.py`
in the Playbook source, copied byte-for-byte by the package builder's sync step.
Native supplies a compact request instead of the governed prompt renderer.
The runner owns the fresh session, read-only sandbox, timeout, report/trace checks,
workspace drift check and hash-linked evidence. It never installs a runtime globally.

On Windows, macOS and Linux, review requires an available Python and Codex CLI.
A Codex desktop login alone does not prove CLI availability; check it in the actual
session. Missing dependencies must be visible in the final result. The package
cannot guarantee execution where the host prohibits subprocesses or reading files.

Native snapshots exclude `.git`, `.playbook-artifacts`, dependency/virtualenv trees
and Python caches. They detect source-file changes, not all filesystem activity.
The sandbox remains the execution boundary. Reviewer findings still require judgment.
Earlier token savings belong to the recorded Role Runner experiments; this portable
Native integration does not promise the same percentage on every task.
