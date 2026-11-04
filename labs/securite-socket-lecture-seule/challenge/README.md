# Functional contract: securite-socket-lecture-seule

Both checks inspect the effective state on the `docker.lab` host. They reject
the initial state and pass only once the capability has been removed. Each
measures one thing, and neither compares file names.

## 1. No mount grants access to the daemon socket

The **daemon's** view: for every mount of the container, the source is resolved
on the host with `readlink -f`, then compared to the resolved socket.

Two ways of reaching the socket are rejected, and the second is the broader
one: **being** that file, or being a **directory that contains it**. Mounting
`/run` whole hands `/run/docker.sock` to the inside without any written path
looking like a socket.

Resolution matters. On the lab VM, `/var/run` is a link to `/run`:
`src=/run/docker.sock` and `src=/var/run/docker.sock` name the same file under
two spellings, and a check comparing strings would let one through.

## 2. The daemon socket is unreachable from inside the container

The **container's** view: every unix socket visible inside is collected with
its (device, inode) pair, and none may be the daemon's.

This is the check a name cannot work around. A path is what you typed; the
inode is what the kernel designates. A renamed destination, a parent directory
mounted whole, or a path no list would have anticipated all yield the same pair
as the host socket, because it is the same file.

This check needs a **running** container: a stopped one cannot be inspected
from the inside. That is why the mission asks you to leave it running.

## What is not graded, and why we tell you

The scenario's first step, observing that a stop `POST` travels through a socket
mounted `:ro`, is **not measured**. This is not an oversight: a stop triggered
through the API leaves no trace distinguishing it from a `docker stop` typed on
the host. A check claiming to require it would measure your obedience, not your
understanding.

Three preliminary verifications are not extra requirements: the container
exists, carries its label, and runs. Without them neither check can look at
anything, and a check that could not look must never conclude green. If
resolving the socket or reading its inode fails on the host, the message tells
you it is not your fault.
