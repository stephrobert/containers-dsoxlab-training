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

Fill in the three lines of `/opt/lab-cgroups/reponses.txt`:

```text
chemin=<the ABSOLUTE path of `mesure`'s cgroup, on the host>
memoire_max=<the memory limit that cgroup declares, as it is>
sans_limite=<what the SAME file contains for `libre`>
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
