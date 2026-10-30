# Adding `USER` breaks the application

## The situation

An audit asks that containers no longer run as root. The gesture fits on one
line: add a `USER` to the Dockerfile.

You do it, you rebuild, and the application **stops writing**. The message talks
about permission denied on a directory the Dockerfile created two lines above.

The reflex is then to roll back, or to open the directory to everyone. Both make
the application run again, and both fail the audit.

## The goal

The context is in `/opt/lab-nonroot/appli`. Build the Dockerfile as it stands:
the application runs, writes its journal, and it is root.

Add a `USER`, rebuild, and read the message.

Build `appli:nonroot`, which must:

```text
print its token, run under a NON-ZERO uid by default, and WRITE
have a data directory that BELONGS to it, and that is not open to everyone
declare its user by a NUMERIC UID
```

The brief is also laid down in `/opt/MISSION.md`.

## Why `USER` alone is never enough

`USER` changes the running identity. It changes **no right**.

The directories created before it belong to root, and a non-root process no
longer writes in them. Measured on this machine: `can't create
/donnees/journal.txt: Permission denied`.

The answer is to align the **owner** with the application's user. Not to open
the directory: a directory writable by anyone undoes exactly what going non-root
was meant to achieve, and a check refuses it.

## Why the uid has to be numeric

A `USER appli` is resolved in the `/etc/passwd` **of the image**.

An orchestrator refusing root containers does not read that file: it reads the
image's declaration, and it cannot prove a name is not root. A numeric uid can
be checked without opening anything.

## Two measurements that contradict what is believed

**`docker run --user 0:0` on the non-root image returns uid=0.** The
Dockerfile's `USER` is a default, not a guarantee: whoever launches decides.
That is why the checks run the image **with no identity option at all**: they
measure what it does when nobody decides for it.

**A non-root process listens on port 80** inside a container, measured. It is
often written that root is required for ports below 1024; the engine grants the
capability by default, and the argument falls. So no check bears on ports: that
would measure a belief.

## What is graded

The **system state**, and the **means** as much as the effect. The second check
verifies that the application writes; the third, that it manages to because the
directory is its own, and not because it is open to everyone.

It is the same structure as `troubleshoot-permission-refusee`, where going back
to root is refused although it works.
