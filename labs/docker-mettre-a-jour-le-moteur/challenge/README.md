# Brief

Work on `docker.lab`, in `/opt/dsoxlab-docker-mettre-a-jour-le-moteur` (the
brief is also in `MISSION.md`). The host runs Docker 29.8.2 and a gateway,
`passerelle-sms`, whose data lives in `volume-passerelle`.

Bring the engine to **29.9.2** and leave the host in the state below. Each
requirement is read on the final state, and the first three are false before any
work.

## 1. The engine is in 29.9.2, exactly

Server, client and the `docker-ce` package are in 29.9.2. The repository offers
a newer candidate, which is not the target.

## 2. The engine packages stay held, in the new version

`docker-ce`, `docker-ce-cli` and `docker-ce-rootless-extras` are in 29.9.2, and
the six Docker packages are held, as they were. The other three
(`containerd.io` and the two plugins) are not part of the climb.

## 3. `live-restore` is active, and the log options are still there

`/etc/docker/daemon.json` carries `"live-restore": true` **and** the log
options it had at the start. The running daemon reports the setting as active:
a file the daemon has not read protects no container.

## 4. The gateway was never restarted

Same process, same start time, and a heartbeat counter that goes up by one,
without a break, from the first line of its file. This check is only judged
once the engine is in 29.9.2: before that, nothing has touched the gateway.

## 5. The data is intact

The subscriber list in the volume is identical to the starting one, byte for
byte. Judged like the previous check, once the engine is in 29.9.2.

## What is not graded

The way back to 29.8.2: the lesson teaches it, this lab does not ask for it.
Nor the backups you take, nor the commands you type: only the final state counts.

Do not remove `passerelle-sms` or its volume, and do not restart them: the
checks compare them with their starting state.
