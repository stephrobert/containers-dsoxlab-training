# docker-mettre-a-jour-le-moteur: move the engine up, and the gateway never notices

## What this lab tests

That you can move Docker Engine from 29.8.2 to 29.9.2 on a host that serves
traffic, without restarting a service and without touching its data. The graded
part is the climb. The way back is taught by the lesson and is not asked here.

## Measured before being written

On `docker.lab`, Debian 13, on 2026-11-09. The engine and its five companion
packages come from the official Docker repository.

| Fact | Value measured |
| --- | --- |
| versions offered for the engine | 29.8.2, 29.9.0, 29.9.1, 29.9.2, 29.9.3 |
| candidate when nothing is named | 29.9.3, not the target |
| packages held by the catalogue baseline | six: `docker-ce`, `docker-ce-cli`, `docker-ce-rootless-extras`, `containerd.io`, `docker-buildx-plugin`, `docker-compose-plugin` |
| daemon restart, gateway with `--restart unless-stopped`, no `live-restore` | the container is stopped, then started again with a new process |
| the same, with `live-restore` read before the climb | same process, same start time, heartbeat counter unbroken |

The last two lines are the lab. Without `live-restore`, the engine climbs and
the gateway restarts, with no message to say so.

## Why three independent measures of a restart

The process number changes, the start time changes, and the heartbeat counter
falls back to 1: a restart shows in the three. A check that read only the
container status would be fooled by a restart policy that brings the container
back by itself.

## Why two checks only count once the engine has climbed

The gateway has not been restarted, and its data is intact: both are true
**before any work**, since the setup has just laid them down. A check true
before the work measures the starting state, not a skill. These two checks
therefore require the engine to be in 29.9.2 first, and say so otherwise.

## Why the log options are checked with the setting

Writing `{"live-restore": true}` over the file turns the setting on and removes
the log options without a word. Both halves are judged together, on the file for
the options and on the running daemon for the setting.

## What the lab does not require

The backups, the validation of the file before the reload, and the way back:
the final state does not prove them, and a check demanding a trace of those
gestures would grade commands.

## The starting state is the repository's rule

The engine is in 29.8.2 and `live-restore` is off, so the first three checks are
false before any work. The cleanup gives the catalogue its own engine back,
in 29.9.2 with six packages held, and removes the `daemon.json` the lab laid down.
