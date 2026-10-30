# The container does not start, and the logs are empty

## The situation

Three in the morning, a backup did not run. The container is stopped. You make
the reflex move, you ask for its logs, and you get **nothing**. Not an error,
not a warning: an empty output.

The image was built yesterday, and the temptation is immediate: it is the image.
You rebuild, you relaunch, and it fails the same way. You spend an hour looking
in the Dockerfile for what is not there.

A container that fails does, however, **always** leave a diagnosis. It simply is
not where you look for it, and the exit code already said where to look.

## The goal

Build yourself the grid. Three containers are stopped, and all three failed for
**three different reasons**:

```text
panne-a   a command that does not exist
panne-b   a file that exists but is not executable
panne-c   a command that runs and fails
```

Two of their exit codes are close enough to be confused, and the third has
nothing to do with them.

Fill in the three lines of `/opt/lab-exit/reponses.txt`:

```text
code_a=<panne-a's exit code>
code_b=<panne-b's exit code>
statut_a=<panne-a's STATUS, as the engine declares it>
```

Then **repair**: start a container named `repare`, **on the same image**, that
runs.

The brief is also written to `/opt/MISSION.md`.

## The third question is the most useful one

Look carefully at `panne-a`'s status. **It is not what you expect from a
container that stopped**, and that says something important about what happened.

Look at all three logs too. One of them says nothing at all, and its diagnosis
is elsewhere: in the container's inspection, a field nobody ever reads.

Those two observations explain each other, and together they explain the lost
hour in the scenario.

## Why the repair uses the same image

Because it is the most profitable conclusion of any troubleshooting: knowing
what is **not** responsible rules out half the leads.

All three failures came from what the container was asked to run, not from what
the image contained. Repairing by changing image would prove the opposite of the
lesson, and the check refuses it.

## What is graded

The **state of the system**. The three expected values are read from the
containers at grading time, and none is written into the checks: the day this lab
changes its failures, they will follow instead of becoming wrong.
