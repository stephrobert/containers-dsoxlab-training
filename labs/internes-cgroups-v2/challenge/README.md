# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running, machine on
unified cgroup v2. Two containers are **already running**, identical except for
one thing:

```text
mesure   started with a memory limit of 256m
libre    started with no limit at all
```

The first three answers go into `/opt/lab-cgroups/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. The path of `mesure`'s cgroup

On the `chemin=` line, an absolute path.

A container's cgroup lives on the **host**, under `/sys/fs/cgroup`, at a path
derived from the container's **full** identifier. Not from its name, not from
its short identifier: the engine gives that identifier.

## 2. The memory limit that cgroup declares

On the `memoire_max=` line, **as it is**.

The kernel only knows bytes: the unit used when setting the limit leaves no
trace. The expected answer is the file's content, unedited and unconverted.

## 3. What the same file contains for `libre`

On the `sans_limite=` line.

Read the **same** file, in the other container's cgroup. You will spontaneously
look for a number, and there is none: it is the lab's most useful question, and
on its own it explains how a container can take all of a machine's memory.

## 4. A `bride` container, with two ceilings

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

## A word on tooling

You have to be root to read a container's cgroup files. That is normal, and it
is not the lab's subject.

And if you prefer to look from the inside: a container sees **its own limit** in
its `/sys/fs/cgroup/memory.max`. That is how a well-behaved application tunes
itself instead of assuming the machine's memory.

## What is not graded

The command you typed. The values can be read in several ways, and both limits
are set at the container's creation, whatever the method. Only the state counts.
