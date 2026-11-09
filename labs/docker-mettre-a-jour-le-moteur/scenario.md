# Move the engine up, and the gateway never notices

## The situation

An SMS gateway has been running on this host for weeks. It writes one heartbeat
per second to a volume, next to the subscriber list it serves, and it comes
back by itself if its container stops.

The engine under it is Docker 29.8.2, installed from the official repository,
with its packages held so that nothing moves it by accident. The maintenance
window is tonight, and the decision is made: **29.9.2**, no other version.

The repository now offers something newer than 29.9.2. Nobody wants that one
tonight.

The team has one condition. The gateway must not restart, not for a second,
and the subscriber list must come out exactly as it went in. Restarting the
daemon is part of any engine update, and a container that comes back after a
daemon restart is a container that was stopped first.

## The goal

The brief is laid down in `/opt/dsoxlab-docker-mettre-a-jour-le-moteur/MISSION.md`.
The gateway container is `passerelle-sms`, its volume `volume-passerelle`.

Bring the engine to **29.9.2 exactly**, and leave the host in this state:

```text
engine         Docker 29.9.2, server and client, the engine packages in that version
packages       the six Docker packages held, as before
live-restore   active, the daemon having read it, the log options of the original
               configuration still there
gateway        never restarted: same process, same start time, heartbeat unbroken
data           the subscriber list identical, byte for byte
```

## What you will find

`/etc/docker/daemon.json` already exists and carries the host's log rotation:
it is configuration that belongs to this host, and it must still be there
afterwards.

The engine is held by `apt-mark hold`: `apt-get` refuses to change a held
package, and it does so on purpose.

## What is graded

The **final state** of the host. How you got there is yours: the checks read
the engine, its packages, its configuration and the gateway, never the
commands you typed.

What is **not** graded is the way back. Going back to the previous version is
taught by the lesson, and it is not asked here.

Nothing in the checks leaves anything behind on the host: the cleanup gives
the catalogue its own engine version back.
