# internes-chaine-dexecution: who really starts a container

## What this lab tests

That a container's process is the child of none of the programs you expect. The
chain, measured on `docker.lab` on 2026-10-30:

```text
sleep (the container's process)
  ← containerd-shim-runc-v2  (one per container)
    ← PID 1                  (the service manager, NOT the daemon)
```

The daemon and the container service are two distinct services, with distinct
PIDs, and **neither is the shim's parent**.

It is the last lab of the internals: after what a container sees, what it may
consume and where its files land, who starts it.

## A received idea the measurement disproved, and it changed the lab

**This lab's first version made the daemon restart** to observe that containers
survive it. The reasoning looked solid: the shim is not the daemon's child, so
the daemon can fall without taking it along.

Measured on 2026-10-30, and the validation caught it by turning the lab RED: the
container's PID **had changed**.

| Moment | container PID | daemon PID |
| --- | --- | --- |
| before the restart | 214470 | 214266 |
| after | **214951** | 214729 |

Without the `live-restore` setting, which is not the default, the daemon stops
its containers on the way out and restarts them. The shim's detachment makes
survival **possible**, it does not **produce** it.

**A lab cannot have a false thing observed.** So the fourth check changed its
move: a second container, and each has its own shim, all detached from the same
parent. It is the same property of the chain, demonstrated differently.

## And one more reason not to touch the daemon

While testing the hypothesis, the repeated restarts hit systemd's limit ("start
of the service was attempted too often"), and the daemon refused to come back
until a `reset-failed`.

A lab restarting a service **three times per validation cycle** would have
broken the same way, and it would have failed for a reason foreign to its
subject. The current move touches no service.

## Why the shim is found by the container's identifier

The machine carries as many as there are containers. A `pgrep` on the program's
name would return the first one found, which would work while a single container
runs and would lie as soon as there are two, that is, exactly when the fourth
check begins.

So the checks look for the command line that **cites the identifier** of the
container in question.

## No PID is written, not even the 1

The shim's parent is **read**, not expected. On a machine set up differently the
detachment could end elsewhere, and this lab would follow instead of becoming
wrong.

The reference solution applies the same rule, and that is what makes it a
demonstration of method rather than a recitation.

## The runtime is read from the right source

Two sources state it: the engine's default, and the container's own. They
coincide on this machine, and would not on a machine with several installed.

The check accepts the **container's**, which is the only true one for this
container.

## The fourth check asks for three facts at once

The second container exists, its shim is **different** from the first, and both
have the **same** parent.

The three do not separate: without the third, two distinct shims could come from
two different chains, and the demonstration would be incomplete.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| `maillon` | running, with its marker | leave it alone | all |
| *nothing* | `maillon-bis` absent | start it | 4 |

## One cleanup move that is not decorative

It makes sure the engine is **up** at the end. The learner may have stopped the
daemon instead of just looking, and the next lab would then start from a machine
with no engine, blaming its own setup.

## What the lab does not require

A path. The shim can be found through the process list as well as the process
tree, the parent through several tools, and the runtime read from two sources.
Only the state counts.
