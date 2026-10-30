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
