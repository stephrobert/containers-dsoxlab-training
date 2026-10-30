# What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The context is
in `/opt/lab-nonroot/appli`:

```text
Dockerfile   it WORKS, and the application runs as root
lancer.sh    it says its identity, and it WRITES a journal
```

**Start by building it as it stands**, then add a `USER` and rebuild. The
identity changes, and the application stops writing. Read the message.

## 1. The image must run under a non-zero uid by default

`appli:nonroot` must print its token and run under a **non-zero** uid, with no
option passed at launch.

The check does not pass `--user`, and that is the only way to measure what the
image decides. Measured on this machine: `--user 0:0` returns uid=0 **on the
non-root image itself**. The Dockerfile's `USER` is a default, not a guarantee.

## 2. The application must keep writing its journal

This is the trap, and it catches everyone once.

`USER` changes the identity and **no right**. The directory created before it
belongs to root, and a non-root process no longer writes in it. The check
measures a real write, not the presence of an instruction.

## 3. The directory must belong to it, without being open to everyone

Two answers make the application write: **giving** it the directory, or
**opening** it to everyone. The second works, and it is refused here.

Making a directory writable by anyone so that an unprivileged process can write
in it undoes exactly what going non-root was meant to achieve. It is the same
structure as `troubleshoot-permission-refusee`, where going back to root is
refused although it works.

## 4. The user must be declared by a numeric uid

A `USER appli` is resolved in the image's `/etc/passwd`.

An orchestrator refusing root containers does not read that file: it reads the
image's declaration, and it cannot prove a name is not root. A numeric uid can
be checked without opening anything.

The check accepts `10001` as well as `10001:10001`, and refuses `appli`.

## A belief this lab does not grade

**A non-root process listens on port 80** inside a container, measured on this
machine. It is often written that root is required below 1024; the engine grants
the capability by default. So no check bears on ports: that would measure a
belief rather than a state.

## What is not graded

The command you typed, nor the uid chosen, nor the user's name. All that counts
is that the uid is non-zero, that the directory is its own, and that the
declaration is numeric.

Mind the order, however: any instruction placed after the `USER` will run under
that identity, and will no longer be able to create or to give.
