# Connect, update, or remove

Connect the current repository with a small, inspectable change. The user's
request to connect authorizes local setup; do not add a second approval step
for the ordinary edits below. Honor existing instructions and permissions.

## Connect

1. Identify the repository root, current branch, uncommitted changes, and
   applicable instructions, including `AGENTS.override.md` and nested files.
   Read the relevant README, package manifest, lockfile, and CI commands.
   Inspect only the project scope needed to find run/check commands.
2. If an established Playbook contract, mandated reviews, or another workflow
   conflicts with Native, explain the concrete conflict and ask which workflow
   should govern. Do not remove or weaken existing requirements as setup.
   Read-only discovery can continue while that decision is pending.
3. Determine how the skills are supplied. When this plugin is installed and
   its skills are discoverable, keep them in the plugin. When invoked by reading
   this file from a separate checkout, copy the enclosing `playbook` skill folder (one level above this reference) and
   its sibling `playbook-frontend` to the project's `.agents/skills/` directory.
   Do not install both copies of the same skill. If names already exist, compare
   them; preserve custom changes and resolve collisions instead of overwriting.
   Do not follow target symlinks to write outside the selected repository.
   Complete and verify skill availability before editing the project block.
   Some hosts protect `.agents` even inside a writable workspace. If the host
   denies installation, stop setup without adding a block that refers to missing
   skills. Report the native plugin install or host approval needed; do not
   retry through a different filesystem route or weaken the sandbox. If this
   attempt already added a block, remove only that new block to restore the
   prior instructions. Partial connection is not successful onboarding.
4. Read [the project block](../assets/project-block.md). Merge it once into the
   effective project instruction file (`AGENTS.md`, or the existing root
   `AGENTS.override.md` that would shadow it). Preserve everything outside its
   markers. For a monorepo, choose the relevant scope without changing sibling
   apps. Add a short adjacent project note only for useful verified facts:
   run/check commands with working directories, design-system location, and
   unusual constraints. Reuse existing notes; do not duplicate them or invent
   scripts. Keep the added note to roughly ten lines.
5. Check actual capabilities: command execution; existing checks; for UI work,
   a reachable browser and screenshot inspection. Prefer an available native
   browser or installed project runner. Report missing capabilities plainly.
   Do not install browser packages, connect accounts, change global settings,
   add MCP, or relax permissions merely to finish setup. A requested first task
   may separately authorize its needed project dependencies.
6. Inspect the diff. Setup is complete when the effective project instructions
   have one block, the two skills have one installation source, and there is a
   usable next task or a specific environment limitation. Do not claim a skill
   was selected or a command passed without observing it. If the client has not
   picked up instructions/skills, start a new session and verify discovery.

Finish with: files changed; commands discovered; capabilities available/missing;
one example task. If the user also supplied a task, continue with it as soon as
setup permits. No brief, task registry, receipts, or policy files are required.

## Update or remove

Only do this when requested. Compare the installed files and marked block with
the requested source version. Preserve user edits; explain unresolved conflicts.
Do not auto-update from a moving branch. With plugin delivery, use the host's
update/remove mechanism instead of adding local duplicates.

Removal removes the Playbook-marked block and disables the skills installed by
this connection. Preserve all user changes. If an installed skill was customized,
move its entire folder, including unchanged references/assets, to a clearly named
backup directory inside the project but outside every skill-discovery root
(for example `.playbook-saved/skills/`). Check that the backup is complete before
removing the active copy. Do not overwrite an existing backup; use a free name
or compare it. Do not leave a customized skill active after claiming removal,
and do not delete its supporting resources while preserving only SKILL.md.
If the host denies the move, leave the original intact and explain the incomplete
removal instead of changing permissions.

For known unmodified installed skills, remove only their owned files. Keep
project-specific notes and all unrelated instructions, tests, screenshots, and
source changes. If an instruction file becomes empty, delete it only if setup
created it. Disabling the plugin alone does not remove the project block;
mention that distinction. Show the diff and the location of any preserved copy.
