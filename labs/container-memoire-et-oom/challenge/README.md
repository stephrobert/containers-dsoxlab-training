# Brief

Work on `docker.lab`, in `/opt/dsoxlab-container-memoire-et-oom`.

1. Keep `worker` active in project `dsoxlab-container-memoire-et-oom`,
   label `dsoxlab.lab=container-memoire-et-oom`.
2. Set RAM and combined RAM-plus-swap budgets to 32 MiB each.
3. Keep OOM killing enabled; effective `memory.max` must be 33554432 and
   `memory.swap.max` must be 0.
4. The checker's bounded exec probe must increment `memory.events`'s oom_kill
   counter while PID 1 remains running.

Keep the pids and CPU guards. No host swap changes or unbounded stress tools.
