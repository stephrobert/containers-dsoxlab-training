# Three containers, three states, and one confusion to clear

## The situation

You arrive on a machine where someone has already been working. Two containers
are there, and they are not in the same state:

```text
vitrine   it is running
rebut     it exists, stopped
```

That second state is the disconcerting one, and it is the subject of this lab:
**a stopped container has not disappeared**. It still holds its name, its logs
are still readable, and it will show up in any listing that is not limited to
running containers. Many people believe they have cleaned up by stopping, then
hit a name already taken without understanding why.

## The goal

Three actions, and nothing more. The image you need is already on the machine:
there is nothing to pull from a registry and nothing to build.

1. **Run** a container named `premier`, which is **running**, and whose logs
   carry the exact line `premier-est-la`.
2. **Stop** `vitrine`, without removing it.
3. **Remove** `rebut`.

The brief also sits on the machine, in `/opt/MISSION.md`.

Mind the first action: a container whose command finishes stops right away.
"Started" is therefore not enough, it has to still be running when we look.

## What is graded

The **state of the engine**, never the commands typed. A running container, the
contents of its logs, a stopped container that still exists, a name that is
gone. The second and third actions are graded **separately**, because that is
exactly where the confusion sits.

Nothing in this lab has to survive a reboot: these are states of the engine,
not of the machine.
