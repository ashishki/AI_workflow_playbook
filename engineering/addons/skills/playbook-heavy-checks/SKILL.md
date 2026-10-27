---
name: playbook-heavy-checks
description: Limit competing heavy test/build commands with an existing heavy CLI on an authorized Linux or macOS machine. Use explicitly for measured resource contention, not every shell command or Windows by assumption.
---

# Queue heavy work, not all work

Check whether overlapping tests/builds actually exhaust the machine. Keep a baseline
of completion time, failures, responsiveness and memory pressure. Read the installed
heavy version/help; pin the tested version in the project or experiment record.
Do not install globally or download the latest installer without permission.

Agree on one user-owned directory on a local filesystem, pool name and slot count
shared by participating checkouts. A different directory/pool is a different queue;
choose capacity from memory/resource measurements, not only CPU count. Wrap selected
expensive commands; leave ordinary file reading and model requests outside the pool.

After verifying flags in that version, use this pattern (replace placeholders):

```text
heavy --dir <shared-local-directory> --pool playbook --slots <agreed-count> --no-skip-ci --timeout <queue-wait-seconds> --on-timeout fail -- <authorized-test-or-build-command>
```

Use the same configuration for every participant. On a shared VPS, CI must not
silently bypass the queue. Do not use `--on-timeout run` or retry outside heavy
to make a check green. The wait timeout is not the execution timeout; retain the
project's bounded execution/cancellation mechanism for the child command.

Check whether HEAVY_HELD/HEAVY_SLOT came from a real parent holding this pool;
nested bypass can exceed the intended concurrency for parallel descendants. Do not
export these markers manually. Propagate the child's actual exit status. Exit 75
may be queue timeout or the child's own result; inspect evidence, do not guess.

heavy is a cooperative semaphore, not memory isolation, a security sandbox or a
fair scheduler. A killed wrapper may release its slot while its child still runs.
Check/stop only owned process groups after cancellation; never kill others' jobs.
Logs can contain commands/paths: no credentials in arguments, no automatic upload.

Compare identical work with/without the queue, including waiting and failures.
Retain it only where contention improves. Missing tool/unsupported OS is BLOCKED
or an explicitly approved sequential fallback, never evidence that heavy worked.
