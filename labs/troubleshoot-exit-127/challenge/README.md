# What is asked

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

## 1. `panne-a`'s exit code

On the `code_a=` line.

This code says nothing about the container or the image: it says a **command**
was not found. The nuance changes the whole diagnosis, because it points at the
name you wrote and not at what you built.

## 2. `panne-b`'s exit code

On the `code_b=` line.

Here the command **was found**, and it still could not be run. The code is a
neighbour of the previous one, and that closeness is what makes them confused:
one points at the command's name, the other at its permissions or its format.

## 3. `panne-a`'s status

On the `statut_a=` line, as the engine declares it.

**Look at it carefully.** It is not the status of a container that stopped, and
that says something important about what happened.

## Look at all three logs too

One of them says **nothing at all**. That is not an anomaly: it is the direct
consequence of the answer to question 3, and its diagnosis is elsewhere, in the
container's inspection, a field nobody ever reads.

Find it. It names the cause in one line, and it is the lost hour of the scenario
that it will save you.

## 4. Repair, on the same image

Start a container named `repare`, **on the same image** as the failures, that
**runs**.

The check verifies both: that it runs, and that it does derive from the same
image. Repairing by changing image would prove the opposite of the lesson.

All three failures came from what the container was asked to run, not from what
the image contained. **Knowing what is not responsible rules out half the
leads.**

## What is not graded

The command you typed. The codes can be read in several ways, and the repair
uses any command that exists and lasts.
