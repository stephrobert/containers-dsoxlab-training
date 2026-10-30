# Who really starts a container

## The situation

You type `docker run`, and a container starts. If asked who started that
process, the spontaneous answer is "Docker". It is wrong, and knowing it changes
the way failures are diagnosed.

At least four programs are involved, and your container's process is the child
of none of the ones you expect. The day the daemon stops answering while the
containers keep running, or the other way round, this chain is what you need in
mind.

## The goal

Walk it, and see where it ends. The container `maillon` is running, and its
process runs `sleep 876543`.

Fill in the three lines of `/opt/lab-chaine/reponses.txt`:

```text
shim=<the PID of the intermediate process that carries THIS container>
parent_du_shim=<the PID of that intermediate process's PARENT>
runtime=<the name of the runtime the engine uses>
```

The second answer is surprising, and that is the point: **look at it twice
before concluding you were wrong.**

Then, to check that this intermediary is indeed **per container** and not
shared, start a second container named `maillon-bis`, and see that it has its
**own** intermediary, with a different PID, but the **same** parent.

The brief is also written to `/opt/MISSION.md`.

## What you will discover

That the intermediary was **detached** from the program that created it. Its
parent is neither the daemon nor the container service: it is the machine's
service manager.

That detachment is deliberate. It makes each container independent of the engine
that started it, and it explains why there is one per container rather than one
for all: a single intermediary would make its fall everyone's fall.

## One received idea not to draw from it

It is tempting to conclude that containers therefore survive a daemon restart.
**That is false by default**, and it was measured on this machine: without the
`live-restore` setting, the daemon stops its containers on the way out and
restarts them, with a fresh PID.

The detachment makes survival **possible**, it does not **produce** it. That is
the kind of nuance that separates an understood architecture from a recited one.

## What is graded

The **state of the system**, and everything is asked of the system at grading
time. No PID is written into the checks or the solution, not even the `1` that
might seem a given: it is **read**, because the detachment could end elsewhere
on a machine set up differently.

PIDs change at every start: there is nothing to copy from a previous pass.
