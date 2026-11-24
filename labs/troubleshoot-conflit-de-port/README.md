# Two port conflicts, two causes

The lesson opposes the port held by a container and the one held by a program
of the host. This course adds five cases that blur this diagnosis: the same
port on two addresses, a publication too wide, a stopped container that loses
its place, a container that `docker ps` does not show as the culprit, and a
`docker-proxy` to be linked to its container.

You work on `essai-*` containers and ports 18400 to 18410. The challenge uses
other containers and ports 18200 and 18201.

Related page: [Publish a Docker port without exposing the whole host](https://www.stephane-robert.info/en/docs/docker/publish-a-port/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run troubleshoot-conflit-de-port
```

You are connected to `docker.lab`, where the engine runs. The `repondeur`
function starts a container that answers one line on its port 80. **Keep the
same terminal until the cleanup**: the variables only exist in it.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
HOTE=$(ip -o -4 route get 1.1.1.1 | awk '{for (i = 1; i <= NF; i++) if ($i == "src") print $(i + 1)}')
repondeur() { docker run -d "$@" "$IMAGE" sh -c 'exec nc -ll -p 80 -e echo "ici $(hostname)"'; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🏠 Exercise 1: the same port on two addresses

Publish port 18400 twice, on two different addresses:

```bash
repondeur --name essai-local -p 127.0.0.1:18400:80 > /dev/null
repondeur --name essai-reseau -p "$HOTE":18400:80 > /dev/null
docker ps --filter name=essai- --format '{{.Names}} {{.Ports}}'
nc -w 3 127.0.0.1 18400
nc -w 3 "$HOTE" 18400
```

```text
essai-reseau 10.10.120.11:18400->80/tcp
essai-local 127.0.0.1:18400->80/tcp
ici b31ec26bbf90
ici abebdc9f35db
```

No conflict: what is unique is the address and the port together. Two different
services therefore answer on the same number, depending on the address called.
A local test can thus succeed on another service than the one seen from the
network.

## 📐 Exercise 2: a publication too wide

Now ask for the same port on all interfaces:

```bash
repondeur --name essai-partout -p 18400:80 2>&1 | grep -o 'Bind for.*'
docker ps --filter name=essai-partout --format '{{.Names}}' | wc -l
```

```text
Bind for 127.0.0.1:18400 failed: port is already allocated
0
```

All interfaces include `127.0.0.1`, already taken. The message names the
address in conflict, not the `0.0.0.0` you asked for: that is the clue. `docker
ps` does not show this container: it has not started.

## 💤 Exercise 3: a stopped container loses its port

Stop `essai-local`, give its port to another one, then try to start it again:

```bash
docker stop --timeout 1 essai-local > /dev/null
repondeur --name essai-remplacant -p 127.0.0.1:18400:80 > /dev/null
docker start essai-local 2>&1 | grep -o 'Bind for.*'
docker container inspect essai-local --format 'statut={{.State.Status}} code={{.State.ExitCode}} erreur={{.State.Error}}' | cut -c1-80
```

```text
Bind for 127.0.0.1:18400 failed: port is already allocated
statut=exited code=143 erreur=failed to set up container networking: driver fail
```

A stopped container does not reserve its port. When started again, it fails
although its configuration has not changed. The status stays `exited` with the
code of the previous stop: only `.State.Error` says that a start has just
failed.

## 👻 Exercise 4: a culprit docker ps does not name

A container started with `--network host` opens its ports directly on the
machine:

```bash
docker run -d --name essai-hote --network host "$IMAGE" nc -lk -p 18410 > /dev/null
sleep 1
repondeur --name essai-refuse -p 18410:80 2>&1 | grep -o 'failed to bind.*'
docker ps --filter publish=18410 --format '{{.Names}}' | wc -l
PID=$(sudo ss -ltnp | grep ':18410' | grep -o 'pid=[0-9]*' | cut -d= -f2)
cat /proc/$PID/cgroup | cut -c1-40
docker container inspect "$(grep -oE '[0-9a-f]{64}' /proc/$PID/cgroup)" --format '{{.Name}}'
```

```text
failed to bind host port 0.0.0.0:18410/tcp: address already in use
0
0::/system.slice/docker-186bf37e6543bf39
/essai-hote
```

The message is the one of a host program, and the `publish` filter finds
nothing. Yet the culprit is a container: the cgroup of its process carries the
container identifier, which `docker container inspect` translates into a name.
Before concluding "outside Docker", read `/proc/<pid>/cgroup`.

## 🧷 Exercise 5: from docker-proxy to the container

`ss` names `docker-proxy` for all published ports. Find the container served by
the one of local port 18400:

```bash
PID=$(sudo ss -ltnp | grep '127.0.0.1:18400' | grep -o 'pid=[0-9]*' | cut -d= -f2)
ps -o args= -p "$PID" | grep -o 'container-ip.*-container-port [0-9]*'
docker ps --filter publish=18400 --format '{{.Names}} {{.Ports}}'
```

```text
container-ip 172.17.0.3 -container-port 80
essai-remplacant 127.0.0.1:18400->80/tcp
essai-reseau 10.10.120.11:18400->80/tcp
```

The command line of `docker-proxy` gives the address and port of the container.
`docker ps` with the filter answers faster, but returns both containers that
publish 18400: the ports column tells them apart.

## 🧹 Cleanup

```bash
docker rm -f essai-local essai-reseau essai-partout essai-remplacant essai-hote essai-refuse > /dev/null
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
sudo ss -ltn | grep -cE ':184(00|10)'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset troubleshoot-conflit-de-port
dsoxlab check troubleshoot-conflit-de-port
```

```text
╭─ Result: troubleshoot-conflit-de-port ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests       │
╰────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two refused containers, two causes, and no
running service to be cut.

```bash
dsoxlab run troubleshoot-conflit-de-port
dsoxlab challenge troubleshoot-conflit-de-port
```
