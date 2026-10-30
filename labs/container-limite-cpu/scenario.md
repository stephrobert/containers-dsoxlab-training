# The application is slow, and yet it has headroom

## The situation

A service runs in a container, capped at half a processor, which is plenty for
what it does. And it is slow. Not down: slow, in fits and starts, with response
times tripling for no apparent reason.

The machine's metrics are calm. The container's show that it consumes exactly
what it was granted, which ought to be reassuring.

The cause is in the application itself, and it is an ordinary one: at startup it
asks the system how many processors are available, and sizes its threads on that
answer. It got the **machine's** number, not its limit's. So it launches twice
as much work in parallel, and spends its time being held back by the kernel.

## The goal

See where the misunderstanding comes from. The container `brideur` is running,
capped at 0.5 CPU, and it does nothing for now.

Fill in the two lines of `/opt/lab-cpu/reponses.txt`:

```text
quota=<what `brideur`'s cgroup declares as its processor time limit, AS IT IS>
cpu_vus=<the number of CPUs `brideur` SEES, from the inside>
```

The second answer is the one that matters, and it is surprising. **Compare it
with the machine's CPU count before concluding you were wrong.**

Then two moves:

1. start a container named `epingle` that sees **only one** CPU. It is not the
   same option, and it is not the same mechanism.
2. put `brideur` under enough load for the kernel to have to **throttle** it.
   Its cgroup counts the throttlings: as long as the counter is zero, the limit
   has never bitten.

The brief is also written to `/opt/MISSION.md`.

## Two mechanisms that get confused

| What you set | What the kernel limits | What the container sees |
| --- | --- | --- |
| a share of CPU | the **time** granted per slice | **everything**, unchanged |
| a set of CPUs | the **processors** usable | fewer |

The first is the one used everywhere, and it is the one that creates the
misunderstanding. The second is rarer, and it is the only one that changes the
answer the system gives the application.

## What is graded

The **state of the system**, and the fourth check asks for a **proof** rather
than a declaration. A limit never seen to bite is a limit taken on trust: it may
well be right, it is not proven.

That is the difference between reading a configuration and observing a
behaviour, and it is the only one that counts the day an application is slow
without anyone knowing why.
