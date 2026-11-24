# A network of your own: naming and isolating

The lesson creates a network, shows its name service, its isolation and the
aliases. This course adds five moves: an overlapping address plan, a fixed
address, a name that disappears, a network that cannot be removed, and a name
that resolves while the connection does not go through.

You work on `essai-*` networks and containers. The challenge uses `avant`,
`arriere` and `tiers`: do not touch them during the course.

Related page: [Default Docker network or your own: which to choose?](https://www.stephane-robert.info/en/docs/docker/default-network-or-your-own/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run reseau-bridge-dedie
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

## 🗺️ Exercise 1: two plans that overlap

Create a network, then a second one whose range contains the first:

```bash
docker network create --subnet 10.88.1.0/24 essai-plan > /dev/null
docker network create --subnet 10.88.0.0/16 essai-recouvre; echo "code: $?"
docker network inspect essai-plan --format '{{(index .IPAM.Config 0).Subnet}}'
```

```text
Error response from daemon: invalid pool request: Pool overlaps with other one on this address space
code: 1
10.88.1.0/24
```

Docker refuses a range that overlaps another one among its networks. The
message does not say which: look for it in the `docker network inspect` of each
network.

## 📌 Exercise 2: a fixed address, asked for twice

On a network whose range you chose, `--ip` sets the address. Ask for it twice:

```bash
repondeur --name essai-fixe --network essai-plan --ip 10.88.1.50 > /dev/null
docker container inspect essai-fixe --format '{{(index .NetworkSettings.Networks "essai-plan").IPAddress}}'
repondeur --name essai-fixe2 --network essai-plan --ip 10.88.1.50 2>&1 | grep -o 'Address already in use'
```

```text
10.88.1.50
Address already in use
```

`Address already in use` is about an IP address here, not a port. The same text
serves both cases: look at what you were asking for. A name is almost always
enough, a fixed address serves a firewall or a device that only knows
addresses.

## 🫥 Exercise 3: a name that disappears

Resolve the name of a member, stop it, then try again:

```bash
docker run -d --name essai-client --network essai-plan "$IMAGE" sleep 600 > /dev/null
docker exec essai-client getent hosts essai-fixe; echo "code: $?"
docker stop --timeout 1 essai-fixe > /dev/null
docker exec essai-client getent hosts essai-fixe; echo "code: $?"
docker start essai-fixe > /dev/null
docker exec essai-client nc -w 3 essai-fixe 80
```

```text
10.88.1.50        essai-fixe  essai-fixe
code: 0
code: 2
ici 7f4906e0e8f2
```

The name service only knows running members. An application that shows "unknown
name" may be aiming at a stopped container, not at a misspelled name. When it
starts again, the name comes back.

## 🔒 Exercise 4: a network that cannot be removed

Try to remove the network while it is in use:

```bash
docker network rm essai-plan 2>&1 | grep -oE 'has active endpoints|essai-(fixe|client)"' | tr -d '"'
docker network inspect essai-plan --format '{{range .Containers}}{{println .Name .IPv4Address}}{{end}}'
```

```text
has active endpoints
essai-client
essai-fixe
essai-fixe 10.88.1.50/24
essai-client 10.88.1.2/24
```

The refusal names the members still attached, which `docker network inspect`
also shows. This is a protection: read the list before you detach anyone.

## 🔇 Exercise 5: resolving is not reaching

A network option forbids members to talk to each other. Create one and try:

```bash
docker network create --opt com.docker.network.bridge.enable_icc=false essai-mute > /dev/null
repondeur --name essai-muet --network essai-mute > /dev/null
docker run -d --name essai-curieux --network essai-mute "$IMAGE" sleep 600 > /dev/null
docker exec essai-curieux getent hosts essai-muet | awk '{print $2}'
docker exec essai-curieux nc -w 3 essai-muet 80; echo "code: $?"
```

```text
essai-muet
code: 1
```

The name resolves and the connection does not go through: the engine's firewall
blocks between members (`enable_icc=false`). When a name answers but the
service does not, look at filtering before accusing the application.

## 🧹 Cleanup

```bash
docker rm -f essai-fixe essai-fixe2 essai-client essai-muet essai-curieux > /dev/null
docker network rm essai-plan essai-mute
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-plan
essai-mute
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset reseau-bridge-dedie
dsoxlab check reseau-bridge-dedie
```

```text
╭─── Result: reseau-bridge-dedie ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a network with a set plan, two containers
that find each other by name on it, and a third left outside.

```bash
dsoxlab run reseau-bridge-dedie
dsoxlab challenge reseau-bridge-dedie
```
