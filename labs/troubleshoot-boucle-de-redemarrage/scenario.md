# One container looping, another the engine gave up on

## The situation

The alert says "container in a restart loop", and that is all. You look, and
indeed: the container list shows one of them starting, failing, starting again.
The engine's journal fills up.

The reflex gesture is to make the noise stop: remove the restart policy, or
destroy the container. Both work, and neither fixes anything. **The policy is
not at fault.** It only makes the failure visible, by repeating it. The
container was already failing on the first try.

And next to it, a second container has the same defect without looping at all:
the engine gave up relaunching it. Two behaviours, one defect, and the policy is
what explains the gap.

## The goal

Three containers, one single defect:

```text
appli-plafond    the engine GAVE UP relaunching it
appli-sans-fin   the engine keeps relaunching it, again and again
appli-saine      runs, and must keep running
```

Read `appli-sans-fin`'s traces first. They say what is missing, and they say it
as many times as there were attempts: that is what makes a looping container's
journal so tedious to read, and it is also the proof that every attempt fails
the same way.

Fill in the three lines of `/opt/lab-boucle/reponses.txt`:

```text
tentatives=<how many times the engine relaunched appli-plafond>
code=<the exit code of appli-plafond>
politique=<the restart policy of appli-sans-fin, as the engine declares it>
```

**Do not repair `appli-plafond`**: the first two answers are read from it, and a
relaunched container starts over, with neither count nor exit code.

The brief is also laid down in `/opt/MISSION.md`.

## Two policies give the very same loop

The third question cannot be guessed. Two different policies produce exactly
the same endless loop, and they differ on one point only, which has nothing to
do with it. So it has to be read, and read **before** repairing: repairing by
removing the policy would make it disappear.

## The repair, and this is where the lab has an opinion

`appli-sans-fin` must **run**, have produced its trace, and **keep its
policy**. And `appli-saine` must be intact, the container of the start.

Lift the cause, and **hand the engine back the wheel**: it catches up on its
own, in about a minute, because it waits between two attempts and that delay
grows. Relaunching the container merely skips the wait.

Removing the policy would be the reflex gesture, and it is the wrong one: the
loop would stop because the container would stop being relaunched, and the
defect would be untouched. Starting from a clean slate would be worse still: it
would carry away a running service, and nothing said it was useless.

## What is graded

The **system state**. The ceiling, the code and the policy are **drawn at
random on each pass**: nothing in the repository carries them, and the checks
recompute them by questioning the engine at grading time.

The fourth check verifies the three halves of the repair: that the container
runs, that its policy is still there, and that the healthy container is the one
of the start, recognised by its identifier and not by its name.
