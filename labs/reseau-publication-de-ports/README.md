# Publishing a port, and only where it belongs

The lesson shows the three scopes of a `-p`, the posture without publication
and the difference between publishing and serving. This course adds five moves:
the protocol, a range of ports, two publications for one container, an address
the machine does not have, and a setting that changes the default.

You work on `essai-*` containers and ports 18300 to 18323. The challenge uses
`vitrine`, `annexe` and `interne`: do not touch them during the course.

Related page: [Publish a Docker port without exposing the whole host](https://www.stephane-robert.info/en/docs/docker/publish-a-port/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run reseau-publication-de-ports
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

## 📨 Exercise 1: TCP is not UDP

Publish the same host port twice, in TCP then in UDP:

```bash
repondeur --name essai-tcp -p 127.0.0.1:18300:80 > /dev/null
repondeur --name essai-udp -p 127.0.0.1:18300:80/udp > /dev/null
docker ps --filter name=essai- --format '{{.Names}} {{.Ports}}'
```

```text
essai-udp 127.0.0.1:18300->80/udp
essai-tcp 127.0.0.1:18300->80/tcp
```

There is no conflict: TCP and UDP numbers are separate. Without a suffix, `-p`
only publishes TCP. A UDP service, such as a DNS server, published without
`/udp`, looks published and answers no one.

## 🎲 Exercise 2: a range of ports, and when it is full

Give a range of two host ports and start three containers:

```bash
for i in 1 2 3; do
  repondeur --name essai-plage$i -p 127.0.0.1:18310-18311:80 > sortie.txt 2>&1
  echo "conteneur $i : code $?"
done
grep -o 'all ports are allocated' sortie.txt
docker ps --filter name=essai-plage --format '{{.Names}} {{.Ports}}'
```

```text
conteneur 1 : code 0
conteneur 2 : code 0
conteneur 3 : code 125
all ports are allocated
essai-plage2 127.0.0.1:18311->80/tcp
essai-plage1 127.0.0.1:18310->80/tcp
```

Docker took the first free port of the range for each. The third is refused
with code 125: the range is full. A range limits what you open, and it empties
when a container is removed.

## 🔀 Exercise 3: two publications for one container

A container can carry several `-p`. Publish it on two addresses, with two
different ports:

```bash
repondeur --name essai-double -p 127.0.0.1:18320:80 -p "$HOTE":18321:80 > /dev/null
docker port essai-double
nc -w 3 127.0.0.1 18320
nc -w 3 "$HOTE" 18321
nc -w 3 127.0.0.1 18321; echo "code: $?"
```

```text
80/tcp -> 10.10.120.11:18321
80/tcp -> 127.0.0.1:18320
ici 6cf1d8a06617
ici 6cf1d8a06617
code: 1
```

The same service answers on two ports, and the port meant for the network stays
closed locally. Each address has its own rule: this is more precise than
publishing on all interfaces.

## 🚫 Exercise 4: an address the machine does not have

Publish on an address that does not belong to this machine, as happens when
copying a command from another server:

```bash
repondeur --name essai-ailleurs -p 10.99.99.99:18322:80 2>&1 | grep -o 'failed to bind.*'
docker container inspect essai-ailleurs --format 'statut={{.State.Status}} code={{.State.ExitCode}}'
```

```text
failed to bind host port 10.99.99.99:18322/tcp: cannot assign requested address
statut=created code=128
```

`cannot assign requested address` comes from the system: no interface carries
this address. It is not a port already taken. The container exists, in state
`created`, and holds its name.

## 🛡️ Exercise 5: change the default of a network

The default of a `-p` without an address is set network by network. Create a
network that publishes on loopback, then publish without an address:

```bash
docker network create --opt com.docker.network.bridge.host_binding_ipv4=127.0.0.1 essai-prudent > /dev/null
repondeur --name essai-prudence --network essai-prudent -p 18323:80 > /dev/null
docker container inspect essai-prudence --format '{{json .HostConfig.PortBindings}}'
docker port essai-prudence
```

```text
{"80/tcp":[{"HostIp":"","HostPort":"18323"}]}
80/tcp -> 127.0.0.1:18323
```

The request carries no address (`HostIp` is empty), and the port is only open
on `127.0.0.1`. `PortBindings` says what was asked, `docker port` what was
done. To know what is open, always read the second.

## 🧹 Cleanup

```bash
docker rm -f essai-tcp essai-udp essai-plage1 essai-plage2 essai-plage3 essai-double essai-ailleurs essai-prudence > /dev/null
docker network rm essai-prudent
rm sortie.txt
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-prudent
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset reseau-publication-de-ports
dsoxlab check reseau-publication-de-ports
```

```text
╭─ Result: reseau-publication-de-ports ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three badly published containers, each to be
put back in the scope that suits it.

```bash
dsoxlab run reseau-publication-de-ports
dsoxlab challenge reseau-publication-de-ports
```
