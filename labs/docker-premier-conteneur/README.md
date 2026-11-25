# Run, stop, remove: three verbs that do not overlap

The lesson runs, lists, stops and removes. This course shows what surprises in
the first days: a name already taken, a container that stops at once, what a
stop keeps, what a removal takes away, and a list that does not show
everything.

You work on `essai-*` containers. The challenge uses `premier`, `vitrine` and
`rebut`: do not touch them during the course.

Related page: [Run a Docker container and choose what it runs](https://www.stephane-robert.info/en/docs/docker/run-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-premier-conteneur
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-debut && cd ~/essai-debut
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🪪 Exercise 1: a name already taken

Start a container that ends at once, then try to take its name again:

```bash
docker run --name essai-nom "$IMAGE" echo bonjour
docker ps --format '{{.Names}}' | grep -c '^essai-nom$'
docker run --name essai-nom "$IMAGE" echo encore 2>&1 | grep -o 'is already in use'
docker rename essai-nom essai-ancien
docker run --name essai-nom "$IMAGE" echo encore
docker rm essai-nom essai-ancien
```

```text
bonjour
0
is already in use
encore
essai-nom
essai-ancien
```

The container is finished, it no longer appears in `docker ps`, and its name is
still taken. It is freed by renaming or removing, never by waiting.

## ⏱️ Exercise 2: a container that stops at once

Start four commands, and read the exit code of each container:

```bash
docker run -d --name essai-a "$IMAGE" true > /dev/null
docker run -d --name essai-b "$IMAGE" sh -c 'echo probleme; exit 3' > /dev/null
docker run -d --name essai-c "$IMAGE" commande-absente 2>&1 | grep -o 'executable file not found'
docker run -d --name essai-d "$IMAGE" /etc/hostname 2>&1 | grep -o 'permission denied' | head -1
docker run -d --name essai-e "$IMAGE" sh > /dev/null
sleep 1
for c in a b c d e; do docker inspect essai-$c --format '{{.Name}} {{.State.Status}} {{.State.ExitCode}}'; done
docker rm essai-a essai-b essai-c essai-d essai-e > /dev/null
```

```text
executable file not found
permission denied
/essai-a exited 0
/essai-b exited 3
/essai-c created 127
/essai-d created 126
/essai-e exited 0
```

A container lives as long as its command. The code says how it ended: 0 for a
normal end, another for an error, 127 for a command not found, 126 for a file
that cannot be executed. The last two never started. A shell without a terminal
has nothing to read and ends too.

## ⏸️ Exercise 3: what a stop keeps

Write a file, stop the container, read its logs, copy the file, then start
again:

```bash
docker run -d --init --name essai-garde "$IMAGE" sh -c 'echo depart; sleep 600' > /dev/null
docker exec essai-garde sh -c 'echo note > /root/note'
docker stop --timeout 1 essai-garde > /dev/null
docker logs essai-garde
docker cp -q essai-garde:/root/note . && cat note
docker exec essai-garde true 2>&1 | grep -o 'is not running'
docker start essai-garde > /dev/null
docker exec essai-garde cat /root/note
docker logs essai-garde
```

```text
depart
note
is not running
note
depart
depart
```

When stopped, the files and logs remain. One can read and copy, not execute. On
restart, it is the same container: the file is there, and the log continues,
hence the two lines.

## 🗑️ Exercise 4: what a removal takes away

Try to remove the running container, then stop it, remove it and make another
one:

```bash
docker rm essai-garde 2>&1 | grep -oE 'container is running|cannot remove container' | head -1
docker stop --timeout 1 essai-garde > /dev/null && docker rm essai-garde
docker logs essai-garde 2>&1 | grep -o 'No such container'
docker run --name essai-garde "$IMAGE" ls -A /root | wc -l
docker rm essai-garde > /dev/null
docker run --rm --name essai-jetable "$IMAGE" echo fini
docker ps -a --format '{{.Names}}' | grep -c essai-jetable
```

```text
cannot remove container
essai-garde
No such container
0
fini
0
```

Removing takes away the container's files and its logs; the new one starts from
the image. Docker refuses to remove a running container, and `-f` lifts that
refusal: do not type it out of habit. `--rm` removes as soon as it ends, along
with the logs.

## 🔎 Exercise 5: a list that does not show everything

Create three containers in three states, and ask for the list in four ways:

```bash
docker run -d --init --name essai-vivant "$IMAGE" sleep 600 > /dev/null
docker create --name essai-jamais "$IMAGE" true > /dev/null
docker run -d --name essai-fini "$IMAGE" sh -c 'exit 4' > /dev/null; sleep 1
echo "ps : $(docker ps --filter name=essai- --format '{{.Names}}' | sort | tr '\n' ' ')"
echo "ps -a : $(docker ps -a --filter name=essai- --format '{{.Names}}:{{.State}}' | sort | tr '\n' ' ')"
echo "sortis en 4 : $(docker ps -a --filter name=essai- --filter exited=4 --format '{{.Names}}')"
echo "jamais lances : $(docker ps -a --filter name=essai- --filter status=created --format '{{.Names}}')"
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
```

```text
ps : essai-vivant
ps -a : essai-fini:exited essai-jamais:created essai-vivant:running
sortis en 4 : essai-fini
jamais lances : essai-jamais
```

`docker ps` only shows what runs. `-a` adds the finished ones and those that
never started. Filters avoid removing by eye: first look at what the filter
returns, then pass it to `docker rm`.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-debut
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-premier-conteneur
dsoxlab check docker-premier-conteneur
```

```text
╭─ Result: docker-premier-conteneur ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three containers, three states, and a name to
free.

```bash
dsoxlab run docker-premier-conteneur
dsoxlab challenge docker-premier-conteneur
```
