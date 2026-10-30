# container-limite-cpu: capping, and proving it

## What this lab tests

That there are **two** ways to limit a container's processor, that they do not
have the same effect, and that the most used one changes **nothing** in what the
container believes it has.

## Measured before being written

On `docker.lab`, a 2-CPU machine, on 2026-10-30:

| Option | `cpu.max` | `cpuset.cpus` | `nproc` **inside** the container |
| --- | --- | --- | --- |
| none | `max 100000` | all | 2 |
| `--cpus 0.5` | `50000 100000` | all | **2** |
| `--cpuset-cpus 0` | `max 100000` | `0` | **1** |

And under two infinite loops: the engine reported **48.97%**, the cgroup counted
**85 throttlings**.

## The subject's trap is on the second line

A **time** limit is not a **view** restriction. The container capped at half a
CPU still sees two.

So an application sizing its threads on that number launches twice too many, and
spends its time being throttled. **That is a real cause of unexplained
slowness**, and it cannot be guessed: the machine's metrics are calm, the
container's show it consuming what it was granted.

The lab has the question asked of the container itself, because that is the only
way to see the misunderstanding rather than learn about it.

## The fourth check asks for a proof, not a declaration

The cgroup counts the throttlings. As long as `nr_throttled` is zero, the limit
has **never bitten**: it may well be right, it is not proven.

That is the difference between reading a configuration and observing a
behaviour. A lab satisfied with reading `cpu.max` would have validated a
theoretical limit, which is exactly what operations cannot afford.

## Two loops, and not one

The load is the lab's most delicate move, and it deserves its explanation.

The first loop consumes what the limit grants; the second forces the throttling.
**A single one could stay under the ceiling** on a fast machine, and the counter
would stay at zero, which would look like a broken lab.

So the reference solution launches two, and stops them afterwards: leaving them
running would keep the machine hot for the next lab, which the validation cycle
runs three times.

## A tooling trap, measured

`pkill -f 'while :'` **kills itself**: the pattern also matches the shell
carrying the command, and that shell is killed before it can return 0. The code
obtained is 143, that is, a SIGTERM received, and `|| true` changes nothing.

So the solution explicitly accepts 0 and 143, stating why. Masking the code
would have been shorter and would have hidden a useful fact: that 143 is the
proof the cleanup happened.

## No value is hardcoded

The expected quota is read in the cgroup, the CPU count is asked of the machine,
and the third check only requires that the pinned container see **fewer**.

A test carrying `50000 100000` or `2` would be wrong on a differently equipped
machine. And on an eight-CPU machine, pinning to two is as right an answer as
pinning to one: the lab does not forbid it.

## Two preconditions that avoid accusing the learner

The machine must be on cgroup v2, otherwise the file names differ. And it must
offer **at least two CPUs**: on a single-processor machine, pinning would change
no view, and the third check would be true before any work.

The setup verifies both before setting the lab.

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | two keys, two **empty** values | fill them in | 1 and 2 |
| `brideur` | capped, **at rest** | put it under load | 4 |
| *nothing* | `epingle` absent | start it pinned | 3 |

At rest, precisely so that the throttling counter is zero and the learner's work
shows up there. The setup verifies it.

## What the cleanup must remove

The containers, and **the counter is what makes it indispensable**: it lives in
the cgroup, and the cgroup goes with the container. If it survived, the fourth
check would be true on the next pass before any work.

## What the lab does not require

A path. The load can come from a shell loop as well as any saturation tool, and
both limiting options are set at the container's creation, however that is done.
