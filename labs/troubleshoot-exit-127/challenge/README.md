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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. **Three
containers are stopped**, and all three failed for three different reasons:

```text
panne-a   a command that does not exist
panne-b   a file that exists but is not executable
panne-c   a command that runs and fails
```

Two of their exit codes are close enough to be confused, and the third has
nothing to do with them.

The first three answers go into `/opt/lab-exit/reponses.txt`, one line per
entry, with no spaces around the equals sign.

The brief is also written to `/opt/MISSION.md`.

### 1. `panne-a`'s exit code

On the `code_a=` line.

This code says nothing about the container or the image: it says a **command**
was not found. The nuance changes the whole diagnosis, because it points at the
name you wrote and not at what you built.

### 2. `panne-b`'s exit code

On the `code_b=` line.

Here the command **was found**, and it still could not be run. The code is a
neighbour of the previous one, and that closeness is what makes them confused:
one points at the command's name, the other at its permissions or its format.

### 3. `panne-a`'s status

On the `statut_a=` line, as the engine declares it.

**Look at it carefully.** It is not the status of a container that stopped, and
that says something important about what happened.

### Look at all three logs too

One of them says **nothing at all**. That is not an anomaly: it is the direct
consequence of the answer to question 3, and its diagnosis is elsewhere, in the
container's inspection, a field nobody ever reads.

Find it. It names the cause in one line, and saves you the lost hour described
above.

### 4. Repair, on the same image

Start a container named `repare`, **on the same image** as the failures, that
**runs**.

The check verifies both: that it runs, and that it does derive from the same
image. Repairing by changing image would prove the opposite of the lesson.

All three failures came from what the container was asked to run, not from what
the image contained. **Knowing what is not responsible rules out half the
leads.**

## What is graded

The **state of the system**. The three expected values are read from the
containers at grading time, and none is written into the checks: the day this lab
changes its failures, they will follow instead of becoming wrong.

### What is not graded

The command you typed. The codes can be read in several ways, and the repair
uses any command that exists and lasts.
