# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **No container
is running**: you start them yourself, because both of the lab's settings are
only set at **creation**.

The image `lab-ulimits:1.0` is ready.

The first two answers go into `/opt/lab-ulimits/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. The default size of `/dev/shm`

On the `shm_defaut_mo=` line, **in megabytes, with no unit**.

Start a container **with no option at all** and ask it. It is a value that is
plenty for almost everything and not enough for a database, which uses it for
its sort buffers.

The symptom, the day it runs short, is an error message about shared memory,
with no apparent connection to a container.

## 2. The default file descriptor limit

On the `nofile_defaut=` line, as the container declares it.

The same container answers it. **The value is surprising by its size: it is not
a reading error.**

The descriptor limit is not modern containers' problem. Its **lowering** is, and
knowing where you start from is what lets you recognise a setting inherited from
another era.

## 3. An `etroit` container, with both settings

Start it with:

```text
a /dev/shm of 256 Mo, and a limit of 1024 file descriptors
```

Both are verified **inside** the container, and that is deliberate: it is the
only place where both are true at once.

The shared memory size is a **mount**, which the inspection also declares. The
descriptor limit is a **ulimit**, which the process carries itself, and which
only the container can state.

## 4. Write 128 Mo into its shared memory

Then look at its **cgroup's memory**.

`/dev/shm` is a tmpfs, therefore memory, and that memory is counted in the
container's cgroup. The check weighs both sides and compares them.

**That is the lab's lesson**: shared memory is not a separate space. A memory
limit must take the size of `/dev/shm` into account, otherwise the container
gets killed for memory it believed was outside.

**Mind the tool**: a file *allocated* without being written occupies no page,
and neither the filesystem's usage nor the cgroup's memory would rise. Write
real bytes.

## A word on tooling

You have to be root to read a container's cgroup files.

And if your first two measurements look odd, take them again: they are right,
and they are remeasured the same way at grading time.

## What is not graded

The command you typed. Both settings can be set on the command line as well as
through the API. Only the state counts, and the weighing is part of it.
