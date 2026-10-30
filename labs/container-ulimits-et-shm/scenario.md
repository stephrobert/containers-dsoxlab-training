# The database dies, and its memory limit looked generous

## The situation

A database runs in a container, with a 512 Mo memory limit. It uses 300 in
steady state, which leaves headroom.

It gets killed by the kernel once a week, on every big report. The
application's metrics show 300 Mo at the moment of death. The container's show
512.

The gap is in **shared memory**. The database uses it for its sort buffers, it
writes several hundred megabytes there during the report, and that memory is
counted in the container's. The application knows nothing about it: to it,
`/dev/shm` is a filesystem, not memory.

At the same time, another service refuses connections complaining about file
descriptors, on a machine that is not short of them at all.

## The goal

Measure those two settings nobody ever looks at, then set them. **No container
is running**: you start them yourself, because both are only set at creation.

The image `lab-ulimits:1.0` is ready.

Fill in the two lines of `/opt/lab-ulimits/reponses.txt`, by starting a
container **with no option** and questioning it:

```text
shm_defaut_mo=<the default size of /dev/shm, IN MEGABYTES, with no unit>
nofile_defaut=<the default file descriptor limit, as the container declares it>
```

The second answer is **surprising by its size**. It is not a reading error.

Then start a container named `etroit` with **two** settings:

```text
a /dev/shm of 256 Mo, and a limit of 1024 file descriptors
```

Finally, write **128 Mo** into its `/dev/shm`, and see what that does to its
**cgroup's memory**.

The brief is also written to `/opt/MISSION.md`.

## Two mechanisms that are not from the same family

Cgroups cap **from the outside**: the kernel counts and refuses. Ulimits are a
POSIX mechanism, far older, which **the process carries itself**.

Looking for both in the same place is the mistake this lab lifts: the shared
memory size can be read from the container's inspection and from its
filesystem, the descriptor limit **only** from the inside.

## The fourth check's lesson

`/dev/shm` is a **tmpfs**, therefore memory, and that memory is counted in the
container's cgroup.

So a memory limit must take the size of `/dev/shm` into account, otherwise the
container gets killed for memory it believed was "separate". That is the
scenario's incident, and it is a cause of death that appears in no application
documentation.

## What is graded

The **state of the system**. Both default values are **remeasured** at grading
time, on a fresh container: the day Docker changes its defaults, these checks
will follow instead of becoming wrong.

And the fourth measurement is a **weighing**: `/dev/shm`'s usage on one side,
the cgroup's memory on the other, and the comparison of the two.
