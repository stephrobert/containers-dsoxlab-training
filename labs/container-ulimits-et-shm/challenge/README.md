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

The second answer is **more modest than you would expect**: the soft limit is
low, while the hard ceiling is very high. The gap between the two is what makes
the question worth asking.

Then start a container named `etroit` with **two** settings:

```text
a /dev/shm of 256 Mo, and a limit of 256 file descriptors
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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **No container
is running**: you start them yourself, because both of the lab's settings are
only set at **creation**.

The image `lab-ulimits:1.0` is ready.

The first two answers go into `/opt/lab-ulimits/reponses.txt`, one line per
entry, with no spaces around the equals sign.

### 1. The default size of `/dev/shm`

On the `shm_defaut_mo=` line, **in megabytes, with no unit**.

Start a container **with no option at all** and ask it. It is a value that is
plenty for almost everything and not enough for a database, which uses it for
its sort buffers.

The symptom, the day it runs short, is an error message about shared memory,
with no apparent connection to a container.

### 2. The default file descriptor limit

On the `nofile_defaut=` line, as the container declares it.

The same container answers it. **The soft limit is low, and its hard ceiling very
high: the gap between the two is what counts.**

The descriptor limit is not modern containers' problem. Its **lowering** is, and
knowing where you start from is what lets you recognise a setting inherited from
another era.

### 3. An `etroit` container, with both settings

Start it with:

```text
a /dev/shm of 256 Mo, and a limit of 256 file descriptors
```

Both are verified **inside** the container, and that is deliberate: it is the
only place where both are true at once.

The shared memory size is a **mount**, which the inspection also declares. The
descriptor limit is a **ulimit**, which the process carries itself, and which
only the container can state.

### 4. Write 128 Mo into its shared memory

Then look at its **cgroup's memory**.

`/dev/shm` is a tmpfs, therefore memory, and that memory is counted in the
container's cgroup. The check weighs both sides and compares them.

**That is the lab's lesson**: shared memory is not a separate space. A memory
limit must take the size of `/dev/shm` into account, otherwise the container
gets killed for memory it believed was outside.

**Mind the tool**: a file *allocated* without being written occupies no page,
and neither the filesystem's usage nor the cgroup's memory would rise. Write
real bytes.

### A word on tooling

A container's cgroup files are **readable without privilege**: measured on this
machine, they are `r--r--r--` or `rw-r--r--`, and an ordinary account opens them
without `sudo`. **Writing** them does require one, and that is what separates
observing from tuning.

And if your first two measurements look odd, take them again: they are right,
and they are remeasured the same way at grading time.

### What is not graded

The command you typed. Both settings can be set on the command line as well as
through the API. Only the state counts, and the weighing is part of it.
