# docker-cycle-de-vie: restarting is not recreating

## What this lab tests

That a container's states form a **graph**, and that you move through it
without starting over. The previous lab taught three verbs; this one teaches
that a stopped container is restarted, keeps its identity, and keeps what was
written inside it.

## The check that carries the whole lab

Comparing `dormeur`'s identifier with the one the setup recorded **before** any
work. It is the only way to tell "I restarted the container" from "I started
another one with the same name": both give a running container, and only one is
the action being taught.

Here the **route is the competence**, so it is measured. But it is measured by
its fingerprint, never by watching the commands typed: `docker start`,
`docker restart` or a start through the API all reach the same state with the
same identifier, and all three count.

The fingerprint is deliberately left **readable** by the learner in
`/opt/lab-cycle/id-dormeur.txt`. A check you can verify yourself teaches; an
opaque one makes you guess.

## Why the file is not a restatement

A recreated container is blank. The check that reads `/empreinte.txt` therefore
measures the **observable consequence** of the mistake the previous check
detects.

That is what makes the lesson hold without asserting it: a learner who
recreated sees their data vanish, which is exactly the incident the scenario
tells.

## The starting state is broken, and that is the repo's rule

| Laid out by the setup | Starting state | Expected action | Check |
| --- | --- | --- | --- |
| `dormeur` | `exited`, with `/empreinte.txt` | restart it | 1 and 2 |
| `actif` | `running` | pause it | 3 |
| *nothing* | absent | make `sortie` exit with 42 | 4 |

A setup task **verifies** this state before handing over: `dormeur exited`,
`actif running`, no `sortie`. Without it, a badly cleaned previous run would
leave the lab already solved before being laid out.

## A cleanup trap, paid in advance

`docker rm` **refuses** a paused container, and that is precisely the state this
lab asks to produce. So `clean` would fail on the very lab whose subject is
pausing, with a message reporting a refusal without saying why. Hence the `-f`,
and hence that comment in `cleanup.yaml`.

## What the lab does not require

An order. The four actions are independent, and check 2 is the only one that
depends on another, by construction rather than by requirement: it reads a file
in a container that must be running.
