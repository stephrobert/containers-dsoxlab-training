# "The container is isolated", but isolated from what?

## The situation

You present a container architecture, and someone asks whether it is safe. The
answer that comes by itself is: "yes, containers are isolated".

That is true, and it is incomplete to the point of being misleading. A container
is isolated in one direction, and not in the other.

Open the machine's process list: the main process of each container is there,
with its command line in plain sight. Nothing is hidden from the host. What is
isolated is **the container's view**, not the machine.

And out of the seven walls the kernel can raise, Docker raises six by default.
The seventh changes everything, and it is the one this lab makes you find.

## The goal

Look at isolation from both sides. The container `cloisonne` is running, and its
main process runs `sleep 987654`, a command whose only purpose is to be
recognisable.

Fill in the three lines of `/opt/lab-namespaces/reponses.txt`:

```text
pid_hote=<the PID that SAME process carries on the HOST>
ns_pid=<the identifier of `cloisonne`'s PID namespace, of the form pid:[...]>
partage=<the FULL IDENTIFIER of the only namespace `cloisonne` shares
         with the host, of the form name:[...]: the name alone is not
         enough, since it is in the lesson and not on your machine>
```

Then start a container named `indiscret` that **sees** the host's processes, and
therefore its neighbour's `sleep 987654`.

The brief is also written to `/opt/MISSION.md`.

## Where to look

A process's namespaces are read in `/proc/<pid>/ns/`. There are seven, and each
is a link to an inode number: that number is what identifies the wall.

For the third question, comparing is enough: `cloisonne`'s namespaces on one
side, those of the host's process 1 on the other. Six differ. One is identical.

## What is graded

The **state of the system**. The PID changes at every start and the namespace
identifiers at every creation: there is nothing to copy from a previous pass,
and nothing to learn by heart.

The fourth check looks at the **effect** and not the option: your container must
see the neighbour's process, **under the host's PID**. That is what distinguishes
"it sees the host's processes" from "it sees its own", which nothing else
separates.

## Why that third question is worth the detour

The shared namespace is the **users'** one. Docker does not isolate it by
default, which means that user 0 in the container is user 0 on the machine.

That is not a flaw: it is the default setting, documented, and it is what makes
necessary all the other precautions you will see later in the course. You only
properly distrust what you have seen for yourself.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`cloisonne` is **already running**, and its main process runs `sleep 987654`, a
command whose only purpose is to be recognisable.

The first three answers go into `/opt/lab-namespaces/reponses.txt`, one line per
entry, with no spaces around the equals sign.

### 1. The process's PID on the host

On the `pid_hote=` line.

The container's main process is PID 1 **inside**, and it also carries a PID on
the host, since it is one of its processes. Nothing was duplicated: it is a
different numbering of the same object.

The PID changes at every start. There is nothing to copy from a previous pass.

### 2. The identifier of `cloisonne`'s PID namespace

On the `ns_pid=` line, of the form `pid:[...]`.

A namespace has no name: it has an **inode number**, which the kernel exposes
through a link in `/proc/<pid>/ns/`. Giving it presupposes having found where
they live, which is the prerequisite of any investigation into isolation.

Be careful to read the **container** process's, not the host's: the host's would
be the one that namespace is isolated from.

### 3. The namespace shared with the host

On the `partage=` line, the full identifier, of the form `name:[...]`. The
name alone is not enough: it is in the lesson, the inode is only on your
machine, and it is identical on both sides.

There are seven: `pid`, `net`, `mnt`, `uts`, `ipc`, `user`, `cgroup`. **Six
differ between the container and the host. One is identical.**

Compare `cloisonne`'s namespaces with those of the host's process 1. The shared
one is also the one that explains why root in a container is a security subject.

### 4. A container that sees the host's processes

Start a container named `indiscret` that **sees** its neighbour's
`sleep 987654`.

By default a container has its own view of processes and sees only its own. It
has to give that up.

The check verifies that the process is seen **under the host's PID**. That is
what distinguishes "it sees the host's processes" from "it sees its own", which
nothing else separates.

### A word on tooling

`readlink /proc/<pid>/ns/<name>` prints a namespace's identifier. And
`readlink /proc/1/ns/<name>` gives the host's, for comparison.

You have to be root to resolve those links: that is normal, and it is not the
lab's subject.

### What is not graded

The command you typed. The PID can be read from the engine as well as from the
host's process list, and the namespaces through several tools. Only the state
counts.
