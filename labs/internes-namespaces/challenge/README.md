# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`cloisonne` is **already running**, and its main process runs `sleep 987654`, a
command whose only purpose is to be recognisable.

The first three answers go into `/opt/lab-namespaces/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. The process's PID on the host

On the `pid_hote=` line.

The container's main process is PID 1 **inside**, and it also carries a PID on
the host, since it is one of its processes. Nothing was duplicated: it is a
different numbering of the same object.

The PID changes at every start. There is nothing to copy from a previous pass.

## 2. The identifier of `cloisonne`'s PID namespace

On the `ns_pid=` line, of the form `pid:[...]`.

A namespace has no name: it has an **inode number**, which the kernel exposes
through a link in `/proc/<pid>/ns/`. Giving it presupposes having found where
they live, which is the prerequisite of any investigation into isolation.

Be careful to read the **container** process's, not the host's: the host's would
be the one that namespace is isolated from.

## 3. The namespace shared with the host

On the `partage=` line, one name among the seven.

There are seven: `pid`, `net`, `mnt`, `uts`, `ipc`, `user`, `cgroup`. **Six
differ between the container and the host. One is identical.**

Compare `cloisonne`'s namespaces with those of the host's process 1. The shared
one is also the one that explains why root in a container is a security subject.

## 4. A container that sees the host's processes

Start a container named `indiscret` that **sees** its neighbour's
`sleep 987654`.

By default a container has its own view of processes and sees only its own. It
has to give that up.

The check verifies that the process is seen **under the host's PID**. That is
what distinguishes "it sees the host's processes" from "it sees its own", which
nothing else separates.

## A word on tooling

`readlink /proc/<pid>/ns/<name>` prints a namespace's identifier. And
`readlink /proc/1/ns/<name>` gives the host's, for comparison.

You have to be root to resolve those links: that is normal, and it is not the
lab's subject.

## What is not graded

The command you typed. The PID can be read from the engine as well as from the
host's process list, and the namespaces through several tools. Only the state
counts.
