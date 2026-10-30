# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The
`lab-cycle:1.0` image is already present: **nothing to pull, nothing to build**.

```text
dormeur   STOPPED, it carries /empreinte.txt
actif     it is RUNNING
```

## 1. `dormeur` is running again, and it is the SAME container

Its identifier must not have changed. The original one was recorded before you
arrived, in `/opt/lab-cycle/id-dormeur.txt`: you can compare it yourself with
the one the engine shows today.

Bringing it back by recreating it under the same name **does not count**. Both
actions give a running container, and that is exactly what makes the confusion
last: only the fingerprint separates them.

## 2. Its `/empreinte.txt` file is still there

This is the observable consequence of the previous point, and there is nothing
extra to do to get it: a restarted container still has it, a recreated
container is blank.

If this check refuses while you believe you restarted, that is the answer to
your question.

## 3. `actif` is paused

Neither stopped nor removed: **paused**. It is a third state, which pausing
freezes without ending the processes, and it is reversible.

A paused container is neither running nor stopped. That is why it is in this
lab: the life cycle is not a line, it is a graph.

## 4. A `sortie` container has finished, with code 42

It must have **run** then **finished**, and carry exit code `42`.

The code is the one returned by the container's main process, and it
**outlives the container**: it is what an orchestrator reads to decide whether
to restart or to alert. A container still running carries none.

## What is not graded

The command you typed. A stopped container can be restarted several ways, and
so can pausing: the check looks at the state and the identity, not at the
route.
