# Test: bring three containers back into service

Three containers of the same chain are down, and **the three failures are
independent**.

## What is observed

That is all that is observed, and none of the three findings states the cause.

1. `collecteur` has **exited**, and nobody has read its exit code.
2. `expediteur` **restarts endlessly**.
3. `scribe` takes **ten seconds** to stop, and its report is **cut off**.

## The five checks

They are of equal weight, and each rests on a verifiable fact.

### 1. The collector runs, from the provided image

Nothing was restarting it, so nothing was hiding the cause: its exit code and
its logs state it. The image is checked as well as the state: rebuilding one of
your own would fix the symptom and lose the lesson.

### 2. The forwarder no longer restarts, and keeps its policy

**The policy is not the failure**: it is what made the failure visible. Removing
it hides the symptom without fixing anything, and the brief asks for it to be
kept.

Stability is measured **over time**: the check reads the restart counter twice,
twelve seconds apart. A counter read once says nothing, since it is zero on a
container that has just been recreated.

### 3. The complete report is copied onto the host

**This is the critical requirement: no total makes up for it.** The report lives
inside the container, and a container does not survive its own removal. A copy of
a truncated report is still a truncated report: it is the data that is lost, not
the file.

### 4. No container of the lab is left stopped

A stopped container keeps its name, its configuration and its disk space. Those
are the ones that fill a disk with nobody knowing where they came from.

### 5. The scribe stops in an orderly way, and its report is whole

**Three facts, one single cause, hence one single check.** `docker stop` sends
`SIGTERM`, waits ten seconds, then `SIGKILL`. A program that gets its signal
stops at once, writes its closing line and exits 0. A program that does not
consumes the whole delay, exits 137, and its writing is truncated.

**This check is played last because it stops the scribe**: a shutdown is only
measured by shutting down, and no reading after the fact replaces it.

## What is provided

The `lab-trois-pannes:1.0` image carries all three roles. Nothing to build. It
reads the `ROLE` variable, and each role has its own requirements.

## The marking

Five checks of equal weight, pass mark **75 out of 100**, and **only the final
state counts**.

Four hints, from the vaguest to the most explicit, and **they cost points**:

```bash
dsoxlab hint
```
