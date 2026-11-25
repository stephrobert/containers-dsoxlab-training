# An OOM that stays in its container

## The situation

The `worker` service runs with 96 MiB of memory. Its deployment contract grants
it 32, without swap. You must bring it back within this budget, and check that
an oversized allocation is killed there without taking the service down.

## Mission

On `docker.lab`, the Compose project is in
`/opt/dsoxlab-container-memoire-et-oom`, under the name
`dsoxlab-container-memoire-et-oom`. Keep a single `worker` running, with its
`dsoxlab.lab=container-memoire-et-oom` label and its task and CPU limits.

### 1. The declared limits

`Memory` and `MemorySwap` both equal 33554432, that is 32 MiB. The machine has
no swap: it is the contract that asks to forbid it, not a spill you could
observe here.

### 2. The applied limits

Inside the container, `memory.max` is 33554432 and `memory.swap.max` is 0.

### 3. An oversized allocation is killed

The check runs a limited allocation in the container, which fits under 96 MiB
and not under 32. It must be killed, and the `oom_kill` counter of
`memory.events` must increase. A non-zero exit code is not enough.

### 4. The service survives

After an OOM caused by this check, `worker` is still running, its `StartedAt`
has not changed, and a file written before the incident can be read.

### What is forbidden

Do not stress the machine, do not change its swap and do not run an unlimited
allocation. If the machine lacks free memory, the check stops and tells you so:
your work is not the cause.
