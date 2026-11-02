# epreuve-contenir-un-conteneur-gourmand: the engine module's test

## What this test measures

Containing a container through its cgroups, and proving the containment holds. It
closes the "Understand what the engine does" module and re-explains nothing.

Its `lab_type: challenge` is what allows its `exam_passing_score`, set to **75**.
The five checks are of equal weight, and one of them is critical.

## The trap, and it is a real one

Setting limits requires **recreating** the container: a cgroup is set at
creation, and changing limits on a running container does not apply them. And
that container mounts a volume holding irreplaceable results.

**So this is a test of care as much as of technique.** Whoever recreates in a
hurry loses the data, and the check does not forgive it: it compares digests, not
names, and a volume recreated empty then refilled by the batch job does not fool
it.

## Why the pointe is bounded, and what deciding that cost

The pointe allocates by doubling until it passes a target, then returns: measured
on this machine on 2026-11-02, it tops out at 256 MB and the host keeps 1.4 GB
free.

The first design used `tail /dev/zero`, which allocates **endlessly**. On a 2 GB
VM, the validation cycle's "before work" pass, where no limit exists yet, would
have had `sshd` or the daemon killed by the host's OOM killer. A test must not be
able to take down the machine that measures it, and a validator that loses its
target returns no verdict at all.

## What the measurement established, and what the pointe check rests on

| Situation | Measured result |
| --- | --- |
| no limit | the allocation succeeds, 536,870,912 bytes, the host holds |
| with 128 MB | the cgroup kills the greedy **child** (`oom_kill 1`), PID 1 survives, the container stays `running` |

The check therefore reads `memory.peak` and `memory.events`. And it requires that
the limit have been **reached**: without that, a learner setting a huge limit
would pass the check without the pointe having tested anything.

## Why "the batch job still answers" is a separate check

Because its cause differs. **Containing is not killing**: a well-set limit kills
the greedy process, not the service. A learner setting an 8 MB limit would
contain the pointe perfectly, and their application would be dead. Merging the
two checks would make that case indistinguishable from a success.

## Why the cgroup is read from inside the container

The scope's path on the host depends on the cgroup driver and the systemd
version, whereas `/sys/fs/cgroup` is mounted inside the container onto its own
cgroup. It is simpler and more portable. And, measured in this catalogue, those
files are readable **without privilege**: writing them does require one, and that
is what separates observing from tuning.

## What the test does not measure

Networking, secrets, hardening. Those are the subjects of other tests.
