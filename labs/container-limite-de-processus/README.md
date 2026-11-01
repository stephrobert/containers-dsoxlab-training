# The pids controller

The cgroup pids controller counts tasks, including threads. Compose's
`pids_limit` becomes Docker's `HostConfig.PidsLimit` and the kernel's
`pids.max`. A shell's `ulimit -u` is a different, per-user mechanism.

For a neutral project `demo-indexer`, compare `pids.current`, `pids.max` and
`pids.events` inside `/sys/fs/cgroup` on a cgroup v2 host. The `max` event counter
increases when a creation is rejected. Existing tasks are not killed simply
because creation would exceed the cap.

Leave room for PID 1, helper processes and diagnostic exec sessions. A ceiling
that prevents all diagnostics is difficult to operate. Test only a finite
burst of short-lived children, never a fork bomb.

This exercise requires cgroup v2 with the pids controller. The checker takes
about five seconds after configuration succeeds. See
[the challenge](challenge/README.md).
