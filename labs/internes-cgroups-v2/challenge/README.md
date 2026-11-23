# A container ate all the machine's memory

## The situation

Three in the morning, the machine stops answering. On reboot, the kernel log
tells the end of the story: the out-of-memory killer struck, and it chose the
database, because it was the biggest consumer at that moment.

The culprit was not the database. It was an image-processing container, started
six months earlier for a trial and never removed. It took all the available
memory, quietly, because **nothing forbade it**.

Nobody had forgotten to set its limit. There was no limit to set: a container
without `--memory` does not have a high ceiling, it has **no ceiling at all**,
and that is very different.

## The goal

Go and see where those limits live, and observe the difference. Two containers
are running, identical except for one thing:

```text
mesure   started with a memory limit of 256m
libre    started with no limit at all
```

The previous lab showed what a container **sees**. This one shows what it may
**consume**, and it is a completely different mechanism: cgroups count and cap,
where namespaces restrict a view.

Fill in the four lines of `/opt/lab-cgroups/reponses.txt`:

```text
chemin=<the ABSOLUTE path of `mesure`'s cgroup, on the host>
memoire_max=<the memory limit that cgroup declares, as it is>
sans_limite=<what the SAME file contains for `libre`>
sans_limite_pids=<what `pids.max` contains for `libre`, in the same
                  cgroup: a container started without any limit still
                  carries a process ceiling, and it is not the same
                  value as for memory>
```

Then start a container named `bride`, with **two** limits at once: 128m of
memory, and 64 processes at most.

The brief is also written to `/opt/MISSION.md`.

## The third question is not a formality

You spontaneously look for a number, and the answer is not one.

That is the whole point of asking it: seeing for yourself what that file
contains when there is no limit explains the scenario's incident better than any
sentence could.

## Why two limits on `bride`, and not one

Because a single one would suggest that memory is the subject. It is only an
example: a cgroup caps memory, processor time, the number of processes,
input/output.

The number of processes protects against a **different** failure, the one that
fills the machine's process table, where a memory limit would change nothing.

## What is graded

The **state of the system**, read in the cgroup and not in the option that asked
for it. What the option asked for is not necessarily what the kernel applies,
and it is the kernel that decides.

The path depends on the container's identifier, which changes at every creation:
there is nothing to copy from a previous pass.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running, machine on
unified cgroup v2. Two containers are **already running**, identical except for
one thing:

```text
mesure   started with a memory limit of 256m
libre    started with no limit at all
```

The first three answers go into `/opt/lab-cgroups/reponses.txt`, one line per
entry, with no spaces around the equals sign.

### 1. The path of `mesure`'s cgroup

On the `chemin=` line, an absolute path.

A container's cgroup lives on the **host**, under `/sys/fs/cgroup`, at a path
derived from the container's **full** identifier. Not from its name, not from
its short identifier: the engine gives that identifier.

### 2. The memory limit that cgroup declares

On the `memoire_max=` line, **as it is**.

The kernel only knows bytes: the unit used when setting the limit leaves no
trace. The expected answer is the file's content, unedited and unconverted.

### 3. What the same file contains for `libre`

On the `sans_limite=` line, and on the `sans_limite_pids=` line the
`pids.max` of the same cgroup: a container without a limit still carries a
process ceiling, which depends on the machine and is in no lesson.

Read the **same** file, in the other container's cgroup. You will spontaneously
look for a number, and there is none: it is the lab's most useful question, and
on its own it explains how a container can take all of a machine's memory.

### 4. A `bride` container, with two ceilings

Start a container named `bride` carrying **two** limits at once:

```text
128m of memory, and 64 processes at most
```

Both must be readable **in its cgroup**, and that is where they are verified:
what the option asked for is not necessarily what the kernel applies.

Two limits and not one, because a single one would suggest that memory is the
subject. The number of processes protects against a different failure: the one
that fills the machine's process table, where a memory limit would change
nothing.

### A word on tooling

A container's cgroup files are **readable without privilege**: measured on this
machine, they are `r--r--r--` or `rw-r--r--`, and an ordinary account opens them
without `sudo`. **Writing** them does require one, and that is what separates
observing from tuning.

And if you prefer to look from the inside: a container sees **its own limit** in
its `/sys/fs/cgroup/memory.max`. That is how a well-behaved application tunes
itself instead of assuming the machine's memory.

### What is not graded

The command you typed. The values can be read in several ways, and both limits
are set at the container's creation, whatever the method. Only the state counts.
