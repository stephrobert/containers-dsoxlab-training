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
