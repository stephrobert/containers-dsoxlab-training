# The container is running, and nobody knows anything about it

## The situation

A contractor delivered a service as a container, started it by hand on this
machine, and then their contract ended. They left no documentation, no
configuration file, no startup script.

The container `greffier` is running. That is about all anyone knows.

You look in `/etc` first, then in `/opt`, then in the shell history. Nothing.
And that is normal: **a running container leaves almost nothing on the host**.
What it said as it started, the address it was given, the port it is reached
on, what it has written since: all of that is held by the engine, and the
engine does not publish it. You have to ask.

This is the most ordinary situation in container troubleshooting, and it
disarms anyone who only has classic-system reflexes.

## The goal

Get four things out of the engine that are written nowhere on this machine.
They are **drawn at random on every pass**: there is nothing to remember, and
nothing to copy from anywhere else.

Fill in the three lines of `/opt/lab-inspection/reponses.txt`:

```text
jeton=<the session token `greffier` announced as it started>
adresse=<the IP address the engine gave `greffier`>
port=<the port of the HOST that the container's 80 is published on>
```

Then take out of the container the file it wrote **after** it started, and put
it down unchanged:

```text
/var/log/greffier/trace.log   ->   /opt/lab-inspection/trace.log
```

The container must **still be running** at the end. The brief is also written
to `/opt/MISSION.md`.

## What is graded

The **state of the system**, never the commands you typed. Each answer is
recomputed at grading time by questioning the engine, then compared with what
you wrote.

So there are several right paths, and all of them count: the token can be read
from the container's output as well as from the log file the engine keeps on
the host, the port from the port table as well as from a full inspection, and
the file can be taken out by a copy as well as by a redirection.

One single move is a mistake, and it costs two checks: **stopping the container
to search it**. A stopped container no longer has an address or a port table.

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`greffier` is **already running**: nothing to pull, nothing to build, nothing
to start.

Four pieces of information concern it, and **none is written on this machine**.
They are drawn at random on every pass: there is nothing to remember, and
nothing to copy from anywhere else.

### 1. The session token

`greffier` announced a token as it started. Write it in
`/opt/lab-inspection/reponses.txt`, on the `jeton=` line.

It is in no configuration file, in no image, and in no script: **the
container's output is the only place it exists**. That is the first question of
any troubleshooting, and also the first command to keep at hand.

### 2. The container's address

The engine gives the container an IP address **when it creates it**. Write it
on the `adresse=` line.

This is the container's own address, not the host's and not the gateway's. It
is reassigned at each creation, so it cannot be remembered: it has to be asked
for.

### 3. The host port

The container's `80` is published on a port of the **host**, and the engine
chose it on its own. Write that port on the `port=` line.

Careful: what is expected is the **host's** port, the one that follows the
arrow. The mapping reads `80/tcp -> 0.0.0.0:32768`: on the left the container's
port, the only value you already knew on arrival, on the right the host's
address and port.

An answer of the form `0.0.0.0:32768` is accepted: it does name the right port.

### 4. The trace, taken out of the container

`greffier` wrote `/var/log/greffier/trace.log` **after** it started. That file
is in no image: it has to be taken out of the container and put down at
`/opt/lab-inspection/trace.log`.

It is expected **unchanged**, not retyped: the trace carries a sequence drawn
at random, which is exactly what cannot be reconstructed by hand.

This is the move you make for real to carry off a log or a fingerprint before
destroying a container.

### The container must still be running at the end

You interrogate a live container, you do not stop it to search it. A stopped
container no longer has an address or a port table: stopping it costs two
checks.

`docker start` puts it back, but its values will have changed: they would have
to be read again.

### What is not graded

The command you typed. Each answer is recomputed by questioning the engine,
then compared with what you wrote. Several paths give the same value, and all
of them count.
