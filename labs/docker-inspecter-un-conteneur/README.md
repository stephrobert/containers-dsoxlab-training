# docker-inspecter-un-conteneur: interrogate a running container

## What this lab tests

That a running container **can be interrogated**, and that each question has
its own command. The previous lab taught the states; this one teaches what can
be known about a container without changing them: what it said, the address it
was given, the port it is reached on, and what it has written since it started.

## The decision that holds the whole lab: the setup knows no answer

All four values are produced **outside the repository**:

| Value | Who produces it | What reveals it |
| --- | --- | --- |
| the session token | the container, from `/dev/urandom` | its logs |
| the trace sequence | the container, from `/dev/urandom` | the file, taken out of the container |
| the IP address | the engine, at creation | inspecting the container |
| the host port | the engine, because `-p 0:80` lets it choose | the port table |

None of them goes through a file in the repository, through the command line,
or through the playbook. **They change on every `run`.** So a learner cannot
find them in the brief, nor copy the ones from a previous pass.

That is what separates this lab from a quiz. The tests recompute each answer by
questioning the engine at grading time, and compare what the learner **claims**
with what the machine **carries**.

## Why four disjoint sources

One per command in the subject: the logs, the inspection, the port table, the
copy of a file.

The trace does **not** carry the session token, and that is deliberate. If it
did, taking the file out would hand over the answer to the first question, and
two checks would measure only one thing. That is the kind of overlap that
inflates a scale without measuring anything more.

## The trap is built, and it is honest

The expected port is the **host's**, not the container's `80`, which is the only
value the learner already knew on arrival. Answering `80` is the surface
mistake, and the check's message names it explicitly rather than saying "wrong
value".

## The starting state is broken, and that is the repository's rule

| Laid down by the setup | Starting state | Expected move | Check |
| --- | --- | --- | --- |
| `reponses.txt` | three keys, three **empty** values | fill them in | 1, 2 and 3 |
| `trace.log` inside the container | absent from the host | take it out unchanged | 4 |

A setup task **verifies** that state before handing over: the container is
running, it does publish a port, and the trace is not already on the host.
Without it, a badly cleaned pass would make the lab already solved before being
set.

## What the lab does not require

A path. `docker logs` and the host's log file give the same token; `docker
port`, `docker inspect` and `ss` give the same port; `docker cp` and a
redirection of `docker exec` take out the same file. All three paths count, and
a learner who reaches the right value another way has learned the same thing.

## The one move that costs two checks

Stopping the container to search it. It then loses its address and its port
table, which the engine does not keep. A helper states that cause **once and
clearly**, rather than letting two checks refuse on an empty value: the learner
would look for the mistake in their written answer, and it is not there.
