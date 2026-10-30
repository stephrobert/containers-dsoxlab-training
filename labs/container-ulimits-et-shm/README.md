# container-ulimits-et-shm: two settings nobody ever looks at

## What this lab tests

That two settings nobody ever looks at decide a container's fate, and that they
are **not from the same family**.

Cgroups cap from the outside; ulimits are a POSIX mechanism, far older, which
the process carries itself. Looking for both in the same place is the mistake
this lab lifts.

It closes the limits family, after `container-limite-cpu`.

## Measured before being written

On `docker.lab`, on 2026-10-30:

| Fact | Value |
| --- | --- |
| `/dev/shm` by default | **64 Mo**, and it is a tmpfs |
| `ulimit -n` by default | **1073741816** |
| `--shm-size 64m` | `.HostConfig.ShmSize` = 67108864 |
| `--ulimit nofile=256:256` | `ulimit -n` = 256 **inside** the container |
| 64 Mo written into `/dev/shm` | cgroup's `memory.current` at 67616768 |

## The second value surprises, and that is why it is asked for

The descriptor limit is **not** modern containers' problem: it is enormous by
default. Its **lowering** is what creates one.

A learner who reads that number and thinks they got it wrong has learned
something more useful than a value: they will recognise a setting inherited from
another era, and will not look for a shortage where there is none.

## The major lesson is the fourth check

`/dev/shm` is a tmpfs, therefore **memory**, and that memory is counted in the
container's cgroup. Writing 128 Mo there makes `memory.current` rise by as much.

Consequence: **a memory limit must take the size of `/dev/shm` into account**,
otherwise the container gets killed for memory it believed was "separate". That
is the scenario's incident, and it is a cause of death that appears in no
application documentation.

The check weighs both sides and compares: the filesystem's usage, and the
cgroup's memory.

## No default value is hardcoded

The first two answers are **remeasured** at grading time, on a fresh container
started with no option at all.

Writing `64` and `1073741816` into the tests would work today and would lie the
day Docker changes its defaults: the checks would turn red with no lab broken.
The reference solution applies the same rule.

## One throwaway container answers both questions

Both values are read in the same shell. Two containers would have been twice as
slow for the same result, and that is the kind of detail that counts when a
validation cycle runs three passes.

## Real bytes, and it is measured

The write into `/dev/shm` uses `dd`. A file **allocated** without being written
would occupy no page, and neither the filesystem's usage nor the cgroup's memory
would rise.

It is the same lesson as in `internes-stockage-des-images`, and it is paid for in
the same place: a weighing only measures what was actually written.

## A YAML mistake avoided by a hair, and it deserved its comment

The setup's final verification had to refuse an already present container.
Written `cmd: ! docker container inspect …`, it was **swallowed by the parser**:
in YAML, a `!` at the head of a scalar is a **tag** indicator.

Measured on 2026-10-30: the command became `docker container inspect etroit …`,
that is, the exact opposite of the intended check, and the setup would have
required the container to exist already.

The rest of the catalogue is unaffected: the other negations live in **folded**
scalars, where the `!` is no longer at the head. The thirteen verifications
concerned were reread one by one afterwards.

## Two preconditions that avoid accusing the learner

The machine must be on cgroup v2, and it must have enough **free memory** for the
test: the fourth check asks for 128 Mo to be written in memory, on top of what
the machine already carries.

The setup verifies both before setting the lab.

## The starting state is broken, and that is the repository's rule

No container is running, and the form is empty. It is the lightest setup in the
catalogue, and that is deliberate: both of the lab's settings are only set at
creation, and there is nothing to observe on an already configured container.

## What the cleanup must remove, and what it does not have to

The container, and **that is the lab's demonstration**: its `/dev/shm` is
memory, and that memory goes with it. No file remains on the disk, unlike a
volume, and that is exactly what the fourth check had observed.

## What the lab does not require

A path. Both settings can be set on the command line as well as through the API,
and the write into shared memory by any tool that writes real bytes.
