# The batch job that takes the host down with it

The `traitement` container runs a batch job. At night it runs away: the whole
machine slows down, it eventually gets killed, and it leaves incomplete files
behind. In the morning, nobody knows what was processed.

It writes its results into `/resultats`, carried by the
`dsoxlab-gourmand-resultats` volume. **That volume already holds results, and
they cannot be reproduced.**

## What is expected at the end

1. The container carries **three limits**, visible in its inspection **as well
   as in its cgroup**: memory, CPU, and number of processes.
2. When the pointe is triggered, it is **contained**: the container does not go
   past its own memory limit, and **no host process is killed**.
3. The batch job **still answers** after the pointe.
4. The earlier results are **intact**, and no file in `/resultats` is truncated:
   each carries its closing line.
5. The `/opt/lab-gourmand/releve.txt` file records two facts, one line each:

   ```text
   pid_hote=<the PID, on the host, of the container's PID 1 process>
   runtime=<the engine's default runtime>
   ```

**To trigger the pointe**: create the `/tmp/pointe` file **inside** the
container, then send it a request. The batch job evaluates the trigger after each
request it serves. It is a tool of the lab, not a riddle.

The full brief is also on the machine, in `/opt/lab-gourmand/MISSION.md`.

## One point about the pointe

It is **bounded**: the allocation tops out at 256 MB, and it does not put the
machine at risk even with no limit in place. That is deliberate: a test must not
be able to take down the machine that measures it.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No limit value
is imposed: what is measured is that a limit exists, that the kernel applies it,
and that it contains the pointe without killing the service.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**losing the earlier results fails the test**, even with everything else in
place. That is the trap, and it is a real one: setting limits requires
**recreating** the container, and that is where a volume gets forgotten.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: contain a greedy container

The `traitement` container runs away at night, slows the machine down, gets
killed, and leaves incomplete files. It writes into `/resultats`, carried by a
volume **that already holds results**.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. Three limits, set and applied

Memory, CPU, number of processes. Each is read in **two places**: the inspection
says what the engine **retained**, the cgroup says what the kernel **applies**.
The two can differ, and the case is common: a cgroup is set at the container's
**creation**, so a limit changed on a running container is not applied.

#### 2. The pointe is contained

Reading a limit does not say whether it contains anything. The check triggers the
pointe, then reads `memory.peak` and `memory.events`: the peak must not exceed
the limit, and the limit must have been **reached**, otherwise the pointe did not
happen and the check would measure nothing.

And the host must not have lost any process. That is the real subject: a
container with no limit does not punish itself, **it punishes its neighbour**.

#### 3. The batch job still answers

**Containing is not killing.** A well-set limit kills the greedy process, not the
service. This check is separate from the previous one because its cause differs:
it fails with a perfectly set limit that is simply too low.

#### 4. The earlier results are intact, and nothing is truncated

**This is the critical requirement: no total makes up for it.**

The check compares **digests**, not names: that is what tells "the files are
there" from "the files are intact". A volume recreated empty, then refilled by
the batch job, would carry plausible names and different contents.

#### 5. The record states the host PID and the runtime

The host PID of PID 1 is the **join between the two worlds**: the process that
believes it is number one inside its container carries another number on the
machine, and that is the one you see in `ps`, in `top` and in a kernel log.
Whoever cannot make that join cannot tie a trace on the host back to a container.

The check **recomputes** both values: it keeps neither hard-coded.

### The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**. No limit value is imposed.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
