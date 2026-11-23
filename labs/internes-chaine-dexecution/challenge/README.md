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
pid_du_processus=<the PID of the container's process on the host>
shim_bis=<the PID of the second container's intermediary>
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
`live-restore` setting, a container with no restart policy comes back `exited`,
PID 0, code 137, and it does **not** start again. Only a policy restarts it, and
it then has a fresh PID: `--restart always` and `--restart unless-stopped` do,
no other.

The detachment makes survival **possible**, it does not **produce** it. That is
the kind of nuance that separates an understood architecture from a recited one.

## What is graded

The **state of the system**, and everything is asked of the system at grading
time. No PID is written into the checks or the solution, not even the `1` that
might seem a given: it is **read**, because the detachment could end elsewhere
on a machine set up differently.

PIDs change at every start: there is nothing to copy from a previous pass.

## What is asked

On `docker.lab`, a disposable Debian 13 with the engine running. The container
`maillon` is **already running**, and its process executes `sleep 876543`, a
command whose only purpose is to be recognisable.

The first three answers go into `/opt/lab-chaine/reponses.txt`, one line per
entry, with no space around the equals sign.

**None of the three is in any course.** They are PIDs: they exist only on this
machine, and they are reassigned at every start. A `dsoxlab reset` therefore
invalidates your whole reading, and it has to be redone in full.

### 1. The PID of the intermediary that carries this container

On the `shim=` line.

Between the engine and your container's process, an intermediary carries it.
The machine has **as many as there are containers**: the right one is the one
whose command line cites **this** container's identifier.

It is also, and this is no accident, the parent of the container's process.

### 2. The PID of the container's process on the host

On the `pid_du_processus=` line.

The process running **inside** the container also has a PID **on the host**,
and the engine states it. That is the bottom of the chain.

The first two answers are the two ends of the same link, and the check requires
them to **agree**: the parent of the PID you give here must be exactly the
intermediary you gave above. If it is not, you read one of the two before a
restart.

### 3. The PID of the second container's intermediary

On the `shim_bis=` line.

Start a container named `maillon-bis`, then **redo the same search on it**. Its
intermediary necessarily carries a different PID from `maillon`'s: there is one
per container.

This answer cannot be deduced, it has to be measured a second time. That is the
point.

### 4. One intermediary per container, and the same parent for both

With both containers up, the last check verifies together:

- that the two intermediaries have **different** PIDs;
- that they have the **same** parent;
- and that the runtime the container declares is found in its intermediary's
  **program name**.

Without the second point, two distinct intermediaries could come from two
different chains, and the demonstration would be incomplete. The third one makes
you **observe** which program really creates the container, instead of asking
you to recite it.

That is what lets a container live its own life without the others depending on
it: a single intermediary would make its fall everyone's fall.

And look at the parent twice before concluding you were wrong: neither the
daemon nor the container service is the parent of these intermediaries. They
were **detached** on purpose.

### A conclusion not to draw from it

One readily concludes that containers therefore survive a daemon restart.
**That is false by default.** Measured on this machine, with `live-restore`
disabled: a container with no restart policy comes back `exited`, PID 0, code
137, and it does **not** start again. Only a policy restarts it, and it then has
a fresh PID: `--restart always` and `--restart unless-stopped` do, no other.

Detachment makes survival **possible**, it does not **produce** it.

And do not try to check it by restarting the daemon several times: systemd's
limit eventually refuses the start, and a `reset-failed` is then needed to get
out of it.

### What is not graded

The command you typed. The intermediary can be found through the process list as
well as the process tree, and a process's PID through several tools. Only state
counts.
