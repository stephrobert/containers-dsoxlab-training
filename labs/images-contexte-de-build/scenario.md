# The engine says it cannot find a file that is right there

## The situation

An application no longer builds. The message is plain:

```text
ERROR: ... "/commun/version.txt": not found
```

You go and look. The file is there, readable, in its place. You read it, you
touch it, you rebuild: same message. So you start hunting for a typo, a rights
problem, a mount that vanished. You lose an hour on a file that never went
missing.

It is missing **for the engine**, and that is something else entirely.

## The goal

The repository is in `/opt/lab-contexte/depot`:

```text
appli/        the application, its Dockerfile and its code
commun/       a file SHARED between several applications
secrets/      a production secret
archives/     20 MB nobody needs
```

Build, read the message, and go check that the file exists. Then ask yourself
what the engine, for its part, was able to see.

Get `appli:contexte` running, printing its token **and** the shared version.

**Three constraints, and each one is graded:**

1. `commun/version.txt` stays the **single source**. Copying it into `appli/`
   would fix the build and create the divergence this layout exists to prevent.
2. neither the secret nor the archives get into the image.
3. the build replays from a `construire.sh` script at the root of the
   repository, in **relative paths**.

The brief is also laid down in `/opt/MISSION.md`.

## What the message no longer says

Measured on this machine, the same Dockerfile under both builders:

| Builder | Message |
| --- | --- |
| buildkit, today's default | `"/commun/version.txt": not found` |
| the classic one, `DOCKER_BUILDKIT=0` | `forbidden path outside the build context` |

The second one **named the cause**. The first says "not found", because the `..`
is normalised then dropped: the engine only looks inside the context, and
reports what it sees, not what is there.

That is why so many answers found online talk about a missing file, and why this
lab starts by having you read the message rather than fix it.

## What this lab does not grade, and why

The **weight of the context**. Everywhere you read that a bulky context slows
the build down, and it used to be true. Measured here: with 20 MB of archives in
the repository, `transferring context` reports **2 bytes**, and the image weighs
exactly the size of the base. Buildkit only sends what the `COPY` instructions
need.

Grading transfer time would therefore measure a belief. What stays true, and
what the lab does grade, is that widening the context puts the whole repository
within reach of a `COPY .`, **the secret included**. An image gets handed
around, and whatever enters it leaves with it.

## What is graded

The **system state**, and it is measured by its effect. The checks replay your
`construire.sh` in a **copy** of the repository, once as it stands, once after
changing the shared version: the rebuilt image must carry the new value. That is
what tells a shared file from a frozen copy, and no reading of the Dockerfile is
needed to say it.

Your image is not lost in the process: its tag is set aside for the duration of
the measurement, then given back.
