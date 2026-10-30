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
partage=<the NAME of the only namespace `cloisonne` shares with the host>
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
