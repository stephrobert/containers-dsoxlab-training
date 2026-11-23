# ENOSPC inside a bounded filesystem sandbox

The worker's `/sandbox` is a 16 MiB tmpfs, not a host partition. A finite filler
has consumed its available capacity. `/sandbox/keep.txt` is useful data;
`/sandbox/fill.bin` is disposable.

In `/opt/dsoxlab-troubleshoot-disque-plein`, recover writable space in the
existing `worker`, project `dsoxlab-troubleshoot-disque-plein`, without losing
the receipt or increasing the sandbox limit.

Do not recreate the container to erase its data, resize the sandbox, fill any
host path or run global prune. The checker writes at most 1 MiB inside the
verified sandbox and removes its probe afterward.

## Brief

Work on `docker.lab`, in `/opt/dsoxlab-troubleshoot-disque-plein`, inside the
**existing** `worker` of project `dsoxlab-troubleshoot-disque-plein`.

Two checks only, and that is a constraint rather than a convenience.

### 1. The disposable filler is gone, and the receipt survived

`/sandbox/fill.bin` is absent, and `/sandbox/keep.txt` still holds its
`keep-this-receipt` content.

The two go together because they are the two faces of one requirement:
reclaiming space without throwing away what matters. Emptying the sandbox does
reclaim space, by destroying what the exercise asked you to protect.

### 2. The reclaimed space allows a real write

The check writes one MiB into `/sandbox`, verifies the file actually weighs
1048576 bytes, then removes its probe in every case.

A `df` would not be enough: a `dd` can return success having written less than
asked, and only the file's real size settles it. The setup guarantees the
starting state by requiring a 4 kiB probe to **fail**, so this check does refuse
before any work.

### What is not graded, and why we tell you

Three of this lab's requirements are **already met at the start**: the original
container exists, `/sandbox` is a 16 MiB tmpfs, and the receipt is there. These
are requirements of **preservation**, not goals to reach.

They cannot become separate checks: a check passing before any work would hand
out points for nothing. They live in the guard shared by both checks, which
refuses cheating without granting anything, and its message names the
prohibition you crossed:

- recreating the container, which erases its data instead of reclaiming space;
- raising the sandbox ceiling, which is not reclaiming space;
- pointing it somewhere other than a tmpfs, which would write into a host
  partition.

The ceiling is read inside the container, through `df`, not from the
declaration: the system is what is authoritative.
