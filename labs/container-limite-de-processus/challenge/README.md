# Brief

Work on `docker.lab`, in `/opt/dsoxlab-container-limite-de-processus`.

Keep one active `worker` in project `dsoxlab-container-limite-de-processus`,
with its `dsoxlab.lab=container-limite-de-processus` label. The checker performs
the guarded burst itself; do not run an unbounded stressor.

Four independent checks measure four different things.

## 1. The declared limits carry the task budget

`PidsLimit` is exactly 16, and the memory cap stays positive and no larger than
64 MiB.

The memory guard is checked here rather than in a check of its own, and that is
deliberate: it is set from the start, so a separate check would pass before any
work and hand out points for nothing. Bounding tasks must not cost the memory
guard, but that is a requirement you preserve, not one you satisfy.

## 2. The cgroup actually applies the task cap

Inside the container, `pids.max` is 16.

The previous check reads what was **asked** of the daemon, this one what the
kernel **retained**. It is also what separates a cgroup limit from a shell
`ulimit`: the latter binds only the descendants of the shell that set it and
disappears with it, so it does not bound the service.

## 3. A bounded burst is refused by the kernel

Twenty-four two-second `sleep` children are started, then waited on.
`pids.events`'s `max` counter must **increase**.

This is not a fork bomb: no recursion, no unbounded loop. The number is chosen
to exceed 16 without approaching the starting 32, and that is measured: the
cgroup already holds three tasks before the burst, so 3 + 24 fits under 32 and
overflows under 16. Under 32 the counter stays at 0; under 16 it goes to 1.

A non-zero exit code would prove nothing by itself. Only this counter says the
kernel refused a creation.

## 4. The service survives saturation and keeps its state

Three things, after a burst this check triggers itself: the worker is still
running, its `StartedAt` has not changed, and a receipt written **before** the
burst can be read after it.

A cap that takes PID 1 down at every spike does not protect the service, it
replaces it with a restart. And surviving as a process is not enough: a service
that starts over has lost what it held.

If the worker is down, the message gives its **exit code**, which carries the
diagnosis: a 137 means the kernel killed it for memory, not for tasks.

The check does not sort the two causes itself, and that is measured rather than
chosen. Such sorting would be decoration here: across five memory levels, from
10 to 32 MiB, the twenty-four `sleep` burst never caused an OOM, and below the
start threshold it is the running-service guard that refuses first. Twenty-four
busybox `sleep` processes consume almost nothing.

This check triggers **its own** burst rather than reusing check 3's, and it
verifies for itself that saturation happened: with no incident, survival cannot
be told from nothing having occurred.

## What is not graded, and why we tell you

Three verifications precede the measurements without being requirements: that
exactly one `worker` runs, that it carries its label, and that `pids.events` is
readable. Without them no check can observe anything, and a check that could not
look must never conclude green. When the read fails on a running service, the
message tells you it is not your fault.
