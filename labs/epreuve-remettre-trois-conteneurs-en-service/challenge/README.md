# Three containers down, three different causes

A processing chain runs on this machine, as three containers: `collecteur`
collects, `expediteur` forwards, `scribe` records. This morning all three are
down, and **the three failures are independent**.

**`collecteur` has exited.** It does not restart, and nobody has read its exit
code.

**`expediteur` restarts endlessly.** You can watch it come back, again and
again.

**`scribe` takes ten seconds to stop**, and the report it writes is cut off
before the end.

None of these three findings states the cause. Establishing them is your job,
and they are not the same.

## What is expected at the end

1. `collecteur` is **running**, from the `lab-trois-pannes:1.0` image.
2. `expediteur` is **running**, it no longer restarts, and **its restart policy
   is kept**: the policy is not the failure.
3. `scribe` is **running**, and it stops in an orderly way: a `docker stop` must
   return in **under ten seconds**, with exit code **0 or 143**, and the report
   must be **complete**.
4. The complete report, the run's reference included, is copied **onto the
   host**, into
   `/opt/lab-trois-pannes/diagnostic.txt`.
5. **No container of this lab is left stopped.**

The report is written inside the container, in `/var/log/scribe.txt`. It is
complete when it carries **its opening line and its closing line**.

To get the copy: fix the scribe's failure, stop it in an orderly way, copy its
report, then **start it again**. Check 5 requires that no container be left
stopped.

The full brief is also on the machine, in `/opt/lab-trois-pannes/MISSION.md`.

## What you do not have to write

The `lab-trois-pannes:1.0` image is provided and carries all three roles: there
is **nothing to build**. It reads the `ROLE` variable, and each role has its own
requirements. Its logs and its exit codes state them.

## How you are graded

Five checks of equal weight, and **only the final state counts**. No command is
imposed.

The pass mark is **75 out of 100**. One requirement is made up for by no total:
**a lost or truncated report fails the test**, even with everything else in
place. The first two failures cost time; that one costs data, and lost data does
not come back.

Four hints are available, and **they cost points**: `dsoxlab hint`.

## Test: bring three containers back into service

Three containers of the same chain are down, and **the three failures are
independent**.

### What is observed

That is all that is observed, and none of the three findings states the cause.

1. `collecteur` has **exited**, and nobody has read its exit code.
2. `expediteur` **restarts endlessly**.
3. `scribe` takes **ten seconds** to stop, and its report is **cut off**.

### The five checks

They are of equal weight, and each rests on a verifiable fact.

#### 1. The collector runs, from the provided image

Nothing was restarting it, so nothing was hiding the cause: its exit code and
its logs state it. The image is checked as well as the state: rebuilding one of
your own would fix the symptom and lose the lesson.

#### 2. The forwarder no longer restarts, and keeps its policy

**The policy is not the failure**: it is what made the failure visible. Removing
it hides the symptom without fixing anything, and the brief asks for it to be
kept.

Stability is measured **over time**: the check reads the restart counter twice,
twelve seconds apart. A counter read once says nothing, since it is zero on a
container that has just been recreated.

#### 3. The complete report is copied onto the host

**This is the critical requirement: no total makes up for it.** The report lives
inside the container, and a container does not survive its own removal. A copy of
a truncated report is still a truncated report: it is the data that is lost, not
the file.

That report carries a **reference unique to this run**, written into it at
startup. A scribe destroyed and recreated writes a different one: its report
will look complete and will not be the right one.

#### 4. No container of the lab is left stopped

A stopped container keeps its name, its configuration and its disk space. Those
are the ones that fill a disk with nobody knowing where they came from.

#### 5. The scribe stops in an orderly way, and its report is whole

**Three facts, one single cause, hence one single check.** `docker stop` sends
`SIGTERM`, waits ten seconds, then `SIGKILL`. A program that gets its signal
stops at once, writes its closing line and exits 0. A program that does not
consumes the whole delay, exits 137, and its writing is truncated.

**This check is played last because it stops the scribe**: a shutdown is only
measured by shutting down, and no reading after the fact replaces it.

### What is provided

The `lab-trois-pannes:1.0` image carries all three roles. Nothing to build. It
reads the `ROLE` variable, and each role has its own requirements.

### The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
