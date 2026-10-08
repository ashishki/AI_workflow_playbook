# Controlled delegation

Use this only when a task has genuinely independent workstreams or a long-running
investigation that benefits from parallel evidence. It is an execution strategy,
not a fourteenth lifecycle stage and not a reason to create agents for every task.
The owner talks to one accountable main agent and need not read worker chats.

## Route before dispatch

Choose one route and record the reason briefly:

- **Self** — small or sequential work, one mutable surface, unclear acceptance, or
  delegation would cost more than the task. This is the default for tiny fixes.
- **Delegate** — two or more independent reads, analyses, checks, or separable outputs
  can proceed without competing for the same state.
- **Ask owner** — business meaning, direction/taste, authority, data disclosure,
  spending, publication, or an irreversible consequence is undecided.
- **Stop/escalate** — rules conflict, no safe writer boundary exists, the budget is
  exhausted, or a failed worker blocks a trustworthy result.

Do not use delegation merely to increase activity, session duration or agent count.
Daily production automation is a separate solution-runtime decision; the agents that
build a workflow do not need to remain inside it.

## Dispatch contract

Before starting workers, the main agent keeps a small work map:

- shared outcome and acceptance evidence;
- each workstream's inputs, output, allowed writes and stop condition;
- owner decisions that remain unresolved;
- total budget across workers, retries, review and human attention.

Start the minimum useful number of workers. Default limits for Product and ordinary
Engineering work are at most **three parallel workers** and **depth one**. A worker
must not start another worker unless the owner explicitly chose an extended experiment
and the host actually supports it. Review workers remain read-only and never launch
reviewers.

One writer owns each file, record, database or other mutable area at a time. Prefer
read-only research/audit workers and let the main agent integrate changes. If parallel
writing is justified, use isolated worktrees/branches or non-overlapping owned paths,
then verify the combined result. Workers do not commit, push, publish, spend money,
grant approval or expand permissions.

## Owner checkpoints

Avoid both silent drift and approval noise. The usual meaningful checkpoints are:

1. **Direction** — after the problem/outcome is understood and before an expensive
   branch of work when a wrong interpretation would waste substantial effort.
2. **Representative result** — the smallest real example that lets the owner judge
   usefulness, meaning and taste before the rest is scaled out.
3. **Consequential action** — before external writes, publication, spending, access
   changes or other actions requiring the owner's authority.

Routine allowed local work continues between checkpoints. A small clear task may need
none. Never turn these into three mandatory meetings.

## Integrate and verify

The main agent remains responsible for the whole result. It must inspect worker outputs,
resolve disagreements against source evidence, notice missing/failed workers, run the
relevant checks on the integrated state and report uncertainty. "All workers finished"
is not acceptance.

Keep concise dispatch/return evidence under `.playbook-artifacts/` when the environment
allows it: task, scope, status, material findings, checks, costs if available and any
human intervention. Preserve raw traces locally but do not force the owner to read them.
Do not put secrets or private source data in shared reports.

If a worker fails or returns a confident contradiction, the main agent verifies facts,
does not average incompatible claims, and either replaces the bounded workstream,
continues safely without it, or stops with a clear blocker. On budget exhaustion save
current state and explain what is ready, what remains uncertain and what additional
work would buy.

Give each dispatch a deadline within the total task budget. Repeated waits and a
follow-up to a completed worker do not reset that budget. If a required return never
arrives, record the missing worker, stop or interrupt the bounded workstream, and
save the incomplete result. A correct output file alone does not make the whole run
successful. Text-only decisions do not need an extra ceremonial review; use the
evidence workers for source checks. Required code review remains a separate step.

## Experimental status

Controlled delegation remains conditional until comparison shows better or equal
outcomes with less owner attention at acceptable total cost. For evaluation use the
controlled-delegation experiment; do not infer benefit from agent count, duration or a
successful orchestration demo alone.
