# An OOM confined to one cgroup

The starter worker has a safe 96 MiB ceiling. The deployment contract instead
requires 32 MiB of RAM and no swap, with the OOM killer enabled.

In `/opt/dsoxlab-container-memoire-et-oom`, apply that budget to `worker` in
project `dsoxlab-container-memoire-et-oom`. A bounded allocation probe should be
killed in that container's cgroup while its small PID 1 survives.

The checker verifies both limits and host headroom before allocating. It
observes `memory.events`, not a guessed exit code. Do not stress the host,
disable OOM killing, change host swap or use an unbounded allocator.
The same PID 1 must remain running without restarting and a freshly written
application receipt must remain readable afterward. The trial removes only
its own receipt; preserving it during this incident is not a reboot guarantee.
