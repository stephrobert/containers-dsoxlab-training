# Test: contain a greedy container

The `traitement` container runs away at night, slows the machine down, gets
killed, and leaves incomplete files. It writes into `/resultats`, carried by a
volume **that already holds results**.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. Three limits, set and applied

Memory, CPU, number of processes. Each is read in **two places**: the inspection
says what the engine **retained**, the cgroup says what the kernel **applies**.
The two can differ, and the case is common: a cgroup is set at the container's
**creation**, so a limit changed on a running container is not applied.

### 2. The pointe is contained

Reading a limit does not say whether it contains anything. The check triggers the
pointe, then reads `memory.peak` and `memory.events`: the peak must not exceed
the limit, and the limit must have been **reached**, otherwise the pointe did not
happen and the check would measure nothing.

And the host must not have lost any process. That is the real subject: a
container with no limit does not punish itself, **it punishes its neighbour**.

### 3. The batch job still answers

**Containing is not killing.** A well-set limit kills the greedy process, not the
service. This check is separate from the previous one because its cause differs:
it fails with a perfectly set limit that is simply too low.

### 4. The earlier results are intact, and nothing is truncated

**This is the critical requirement: no total makes up for it.**

The check compares **digests**, not names: that is what tells "the files are
there" from "the files are intact". A volume recreated empty, then refilled by
the batch job, would carry plausible names and different contents.

### 5. The record states the host PID and the runtime

The host PID of PID 1 is the **join between the two worlds**: the process that
believes it is number one inside its container carries another number on the
machine, and that is the one you see in `ps`, in `top` and in a kernel log.
Whoever cannot make that join cannot tie a trace on the host back to a container.

The check **recomputes** both values: it keeps neither hard-coded.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**. No limit value is imposed.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
