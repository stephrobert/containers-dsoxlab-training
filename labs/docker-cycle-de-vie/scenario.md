# The container restarted, but it is no longer the same one

## The situation

An on-call night. A container has stopped, and the runbook says: "restart the
`dormeur` container". You restart it, everything comes back, you go back to
sleep.

The next day, the team finds the container's working files are gone. And yet
you did exactly what was written.

What happened is not a failure at all. "Restart" can mean two actions that look
nothing alike: **restarting** the container that existed, or **creating a new
one** with the same name. Both give a running container, which is what makes
the confusion last. Only one keeps the container's identity, its logs and what
had been written inside it.

## The goal

Move through the life cycle without ever starting over. The image is already on
the machine: nothing to pull, nothing to build.

```text
dormeur   STOPPED, and it carries a /empreinte.txt file
actif     it is RUNNING
```

1. `dormeur` is **running again**, and it is the **same** container: its
   identifier must not have changed.
2. Its `/empreinte.txt` file is still there.
3. `actif` is **paused**, neither stopped nor removed.
4. A container named `sortie` has **finished**, with exit code **42**.

The brief also sits in `/opt/MISSION.md`.

## What is graded

The **state of the engine**, never the commands typed. But here identity counts
as much as state: `dormeur`'s original identifier was recorded **before** you
touched anything, and it is compared. You can read it yourself in
`/opt/lab-cycle/id-dormeur.txt`.

This is not distrust, it is the only way to tell the two actions apart: their
visible result is identical, and only the fingerprint separates them.
