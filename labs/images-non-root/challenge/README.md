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

## What is asked

On `docker.lab`, a throwaway Debian 13 with the engine running. The context is
in `/opt/lab-nonroot/appli`:

```text
Dockerfile   it WORKS, and the application runs as root
lancer.sh    it says its identity, and it WRITES a journal
```

**Start by building it as it stands**, then add a `USER` and rebuild. The
identity changes, and the application stops writing. Read the message.

### 1. The image must run under a non-zero uid by default

`appli:nonroot` must print its token and run under a **non-zero** uid, with no
option passed at launch.

The check does not pass `--user`, and that is the only way to measure what the
image decides. Measured on this machine: `--user 0:0` returns uid=0 **on the
non-root image itself**. The Dockerfile's `USER` is a default, not a guarantee.

### 2. The application must keep writing its journal

This is the trap, and it catches everyone once.

`USER` changes the identity and **no right**. The directory created before it
belongs to root, and a non-root process no longer writes in it. The check
measures a real write, not the presence of an instruction.

### 3. The directory must belong to it, without being open to everyone

Two answers make the application write: **giving** it the directory, or
**opening** it to everyone. The second works, and it is refused here.

Making a directory writable by anyone so that an unprivileged process can write
in it undoes exactly what going non-root was meant to achieve. It is the same
structure as `troubleshoot-permission-refusee`, where going back to root is
refused although it works.

### 4. The user must be declared by a numeric uid

A `USER appli` is resolved in the image's `/etc/passwd`.

An orchestrator refusing root containers does not read that file: it reads the
image's declaration, and it cannot prove a name is not root. A numeric uid can
be checked without opening anything.

The check accepts `10001` as well as `10001:10001`, and refuses `appli`.

### A belief this lab does not grade

**A non-root process listens on port 80** inside a container, measured on this
machine. It is often written that root is required below 1024, and the usual
explanation is wrong: it is not a capability. The effective capabilities of a
process started with `--user 10001:10001` are **empty**, and it still listens
under `--cap-drop ALL`. The engine lowers the threshold itself, inside the
container's network namespace: `net.ipv4.ip_unprivileged_port_start` is `0` there.
Raise it to `1024` and the same container answers `nc: bind: Permission denied`.

The nuance matters: anyone who believes in a capability will reach for
`--cap-add NET_BIND_SERVICE` for a problem that flag does not solve. So no check
bears on ports: that would measure a belief rather than a state.

### What is not graded

The command you typed, nor the uid chosen, nor the user's name. All that counts
is that the uid is non-zero, that the directory is its own, and that the
declaration is numeric.

Mind the order, however: any instruction placed after the `USER` will run under
that identity, and will no longer be able to create or to give.
