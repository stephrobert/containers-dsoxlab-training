# Contain process creation

The worker has a safe starter ceiling of 32 tasks, but its operational budget is
16. A process ceiling must be a cgroup limit, not just a shell's ulimit.

In `/opt/dsoxlab-container-limite-de-processus`, apply the 16-task budget to
`worker` in project `dsoxlab-container-limite-de-processus`. Keep it running and
retain the memory and CPU guards.

The checker launches at most 24 short-lived sleep children, only after verifying
the effective cap. This is not a fork bomb. Never use recursion, unbounded loops
that fork, or host-wide process limits.
After the finite burst ends, the original service must resume without restarting
or losing a freshly written application receipt. Only the trial receipt is removed.
