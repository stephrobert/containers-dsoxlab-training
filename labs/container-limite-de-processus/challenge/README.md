# A service, and no more than sixteen tasks

## The situation

The `worker` service may create up to 32 tasks. Its operating budget is 16. You
must bring it back to that without losing its other limits, and check that a
burst of processes is refused without taking the service down.

## Mission

On `docker.lab`, the Compose project is in
`/opt/dsoxlab-container-limite-de-processus`, under the name
`dsoxlab-container-limite-de-processus`. Keep a single `worker` running, with its
`dsoxlab.lab=container-limite-de-processus` label and its CPU limit.

### 1. The declared limits

`PidsLimit` is 16, and the memory limit stays in place, at 64 MiB at most.

### 2. The applied limit

Inside the container, `pids.max` is 16. A shell `ulimit` changes nothing there.

### 3. A burst is refused

The check starts 24 two-second `sleep` in the container. They fit under 32 and
not under 16. The `max` counter of `pids.events` must increase. A non-zero exit
code is not enough.

### 4. The service survives

After a burst started by this check, `worker` is still running, its `StartedAt`
has not changed, and a file written before the burst can be read.

### What is forbidden

Do not run any endless process-creating loop, and do not set a limit on the
whole machine. The check does the burst itself.
