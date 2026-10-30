# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The container
`maillon` is **already running**, and its process runs `sleep 876543`, a command
whose only purpose is to be recognisable.

The first three answers go into `/opt/lab-chaine/reponses.txt`, one line per
entry, with no spaces around the equals sign.

## 1. The PID of the intermediary carrying this container

On the `shim=` line.

Between the engine and your container's process, an intermediary carries it. The
machine has **as many as there are containers**: the right one is the one whose
command line cites **this** container's identifier.

It is also, and not by chance, the parent of the container's process.

## 2. The PID of that intermediary's parent

On the `parent_du_shim=` line.

**Look at it twice before concluding you were wrong.** The answer is surprising,
and that is the point of the question: neither the daemon nor the container
service is that intermediary's parent.

It was **detached** from it on purpose.

## 3. The runtime in use

On the `runtime=` line.

The engine does not create containers itself: it delegates to a runtime, and
that runtime is a **choice**. Knowing it is what makes it understandable that
another one can be installed, to isolate more strongly or to measure
differently.

Two sources state it: the engine's default, and the container's. The
**container's** is the one asked for, because it is the only true one for this
container.

## 4. A second container, and its own intermediary

Start a container named `maillon-bis`, and see that it has its **own**
intermediary:

- with a PID **different** from `maillon`'s;
- but with the **same** parent.

All three facts are verified together. Without the last one, two distinct
intermediaries could come from two different chains, and the demonstration would
be incomplete.

That is what lets a container live its own life without the others depending on
it: a single intermediary would make its fall everyone's fall.

## One received idea not to draw from it

It is tempting to conclude that containers therefore survive a daemon restart.
**That is false by default.** Measured on this machine: without the
`live-restore` setting, the daemon stops its containers on the way out and
restarts them, with a fresh PID.

The detachment makes survival **possible**, it does not **produce** it.

And do not try to check it by restarting the daemon several times: systemd's
limit ends up refusing the start, and a `reset-failed` is then needed to get
out of it.

## What is not graded

The command you typed. The intermediary can be found through the process list as
well as the process tree, and its parent through several tools. Only the state
counts.
