# A harmless syscall as a measurable boundary

Your team's demonstration policy must reject `getpgid(2147483647)` with EPERM
while allowing `getpgid(0)` and `getpid`. The reserved PID argument targets only
the harmless probe, not runtime initialization. Without the filter, querying
that nonexistent PID returns ESRCH, not EPERM.
The supplied C probe performs only these read-only calls and prints their verdict.

In `/opt/dsoxlab-securite-seccomp`, attach an explicit seccomp filter to
`worker` in project `dsoxlab-securite-seccomp`. The provided JSON currently
allows everything and the starter explicitly uses `unconfined`.

This is a controlled syscall lesson, not a production hardening profile.
Never change daemon defaults or run privileged containers.
