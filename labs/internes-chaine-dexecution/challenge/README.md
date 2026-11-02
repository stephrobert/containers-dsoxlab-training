# What is asked

On `docker.lab`, a disposable Debian 13 with the engine running. The container
`maillon` is **already running**, and its process executes `sleep 876543`, a
command whose only purpose is to be recognisable.

The first three answers go into `/opt/lab-chaine/reponses.txt`, one line per
entry, with no space around the equals sign.

**None of the three is in any course.** They are PIDs: they exist only on this
machine, and they are reassigned at every start. A `dsoxlab reset` therefore
invalidates your whole reading, and it has to be redone in full.

## 1. The PID of the intermediary that carries this container

On the `shim=` line.

Between the engine and your container's process, an intermediary carries it.
The machine has **as many as there are containers**: the right one is the one
whose command line cites **this** container's identifier.

It is also, and this is no accident, the parent of the container's process.

## 2. The PID of the container's process on the host

On the `pid_du_processus=` line.

The process running **inside** the container also has a PID **on the host**,
and the engine states it. That is the bottom of the chain.

The first two answers are the two ends of the same link, and the check requires
them to **agree**: the parent of the PID you give here must be exactly the
intermediary you gave above. If it is not, you read one of the two before a
restart.

## 3. The PID of the second container's intermediary

On the `shim_bis=` line.

Start a container named `maillon-bis`, then **redo the same search on it**. Its
intermediary necessarily carries a different PID from `maillon`'s: there is one
per container.

This answer cannot be deduced, it has to be measured a second time. That is the
point.

## 4. One intermediary per container, and the same parent for both

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

## A conclusion not to draw from it

One readily concludes that containers therefore survive a daemon restart.
**That is false by default.** Measured on this machine, with `live-restore`
disabled: a container with no restart policy comes back `exited`, PID 0, code
137, and it does **not** start again. Only a policy restarts it, and it then has
a fresh PID: `--restart always` and `--restart unless-stopped` do, no other.

Detachment makes survival **possible**, it does not **produce** it.

And do not try to check it by restarting the daemon several times: systemd's
limit eventually refuses the start, and a `reset-failed` is then needed to get
out of it.

## What is not graded

The command you typed. The intermediary can be found through the process list as
well as the process tree, and a process's PID through several tools. Only state
counts.
