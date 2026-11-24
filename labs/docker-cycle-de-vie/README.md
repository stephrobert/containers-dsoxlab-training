# Lifecycle: restarting is not recreating

The lesson shows the states of a container, the difference between restarting
and recreating, the pause and the exit code. This course covers five situations
it does not show: the error message that pushes you to delete, what a restart
loses anyway, reading a stopped container, the commands refused during a pause,
and waiting for a task to end.

You work on `essai-*` containers. The challenge uses other containers, already
on the machine: do not touch them during the course.

Related page: [Container lifecycle, PID 1 and clean shutdown in Docker](https://www.stephane-robert.info/en/docs/docker/container-lifecycle-and-signals/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-cycle-de-vie
```

You are connected to `docker.lab`, where the engine runs. The Alpine image is
already on the machine. **Keep the same terminal until the cleanup**: the
`IMAGE` variable only exists in it.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026. Your container identifiers will differ.

## 🏷️ Exercise 1: the message that pushes you to delete

Start a container, then run the same command again, as one does at night when
copying a runbook. Then rename the container, reading its identifier before and
after:

```bash
docker run -d --name essai-carnet --tmpfs /cache "$IMAGE" sh -c 'sleep infinity' > /dev/null
docker run -d --name essai-carnet "$IMAGE" sh -c 'sleep infinity'; echo "code: $?"
docker container inspect essai-carnet --format '{{.Id}}' | cut -c1-12
docker rename essai-carnet essai-journal
docker container inspect essai-journal --format '{{.Id}}' | cut -c1-12
```

```text
docker: Error response from daemon: Conflict. The container name "/essai-carnet" is already in use by container "e8304bd2cef43df6572373a84ea7c6f18d2b944ef4377d9606b14d5a7a6776ce". You have to remove (or rename) that container to be able to reuse that name.

Run 'docker run --help' for more information
code: 125
e8304bd2cef4
e8304bd2cef4
```

The second `docker run` fails with code 125: the name is already taken. The
message suggests removing the container or renaming it. Removing it would lose
its files, which is the mistake the challenge tells about. To start again what
exists, use `docker start`. And if the name must be freed, `docker rename` does
it without losing anything: both identifiers are the same.

## 💾 Exercise 2: what a restart loses

The container was started with `--tmpfs /cache`, which puts this directory in
memory. Write one file on the container's disk and another in `/cache`, then
restart:

```bash
docker exec essai-journal sh -c 'echo disque > /note.txt; echo memoire > /cache/note.txt'
docker restart --timeout 1 essai-journal
docker exec essai-journal cat /note.txt
docker exec essai-journal cat /cache/note.txt; echo "code: $?"
```

```text
essai-journal
disque
cat: can't open '/cache/note.txt': No such file or directory
code: 1
```

The container is still the same, and `/note.txt` is still there. The file in
`/cache` is gone: a `tmpfs` lives in memory and is emptied at each stop.
Restarting keeps the container's writable layer, not what is in memory.

## 🔎 Exercise 3: read a stopped container

A stopped container keeps its files, but `docker exec` can no longer enter it.
Two commands read it without starting it:

```bash
docker stop --timeout 1 essai-journal
docker exec essai-journal cat /note.txt; echo "code: $?"
docker diff essai-journal
docker cp essai-journal:/note.txt - | tar -xO
docker container inspect essai-journal --format '{{.State.Status}}'
```

```text
essai-journal
Error response from daemon: container e8304bd2cef43df6572373a84ea7c6f18d2b944ef4377d9606b14d5a7a6776ce is not running
code: 1
A /note.txt
A /cache
disque
exited
```

`docker exec` requires a running container. `docker diff` lists what changed
compared with the image: `A` marks an addition. `/cache` is listed because
Docker created this directory to mount the `tmpfs` on it. `docker cp` takes a
file out, here to standard output as an archive that `tar` unpacks. The state
stays `exited`: you read the data without changing anything. Do this before you
decide anything about a stopped container.

## ⏸️ Exercise 4: the commands refused during a pause

Start the container again, pause it, then try four commands:

```bash
docker start essai-journal
docker pause essai-journal
docker exec essai-journal true; echo "exec: $?"
docker start essai-journal; echo "start: $?"
docker rm essai-journal; echo "rm: $?"
docker restart --timeout 1 essai-journal; echo "restart: $?"
docker container inspect essai-journal --format '{{.State.Status}}'
```

```text
essai-journal
essai-journal
Error response from daemon: Container essai-journal is paused, unpause the container before exec
exec: 1
Error response from daemon: cannot start a paused container, try unpause instead
failed to start containers: essai-journal
start: 1
Error response from daemon: cannot remove container "essai-journal": container is paused and must be unpaused first
rm: 1
essai-journal
restart: 0
running
```

`exec`, `start` and `rm` are refused, and each message says to unpause first.
`docker restart` succeeds without a warning: the container is stopped then
started, and is no longer paused. The suspended processes were therefore ended.
To resume where they were, use `docker unpause`.

## ⏱️ Exercise 5: wait for a task to end

A script often needs to wait for a container to finish. `docker wait` blocks
until the end, then shows the exit code. `docker events` reads back what
happened:

```bash
DEBUT=$(date +%s)
docker run -d --name essai-tache "$IMAGE" sh -c 'sleep 2; exit 7' > /dev/null
docker wait essai-tache
docker events --since "$DEBUT" --until "$(( $(date +%s) + 1 ))" --filter container=essai-tache --format '{{.Action}} {{.Actor.Attributes}}' | grep -oE '^(create|start|die)|exitCode:[0-9]+'
```

```text
7
create
start
die
exitCode:7
```

`docker wait` returned after two seconds with code 7. In the events, `create`
and `start` match the `docker run`, and `die` the end of the process, with its
code. This trace tells when, and with which code, a container ended.

## 🧹 Cleanup

Remove the practice containers and check that none is left:

```bash
docker rm -f essai-journal essai-tache > /dev/null
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-cycle-de-vie
dsoxlab check docker-cycle-de-vie
```

```text
╭─── Result: docker-cycle-de-vie ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: bring a stopped container back without
recreating it, pause another one, and make a third one end with a given code.

```bash
dsoxlab run docker-cycle-de-vie
dsoxlab challenge docker-cycle-de-vie
```
