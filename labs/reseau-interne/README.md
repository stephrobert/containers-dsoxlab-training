# Two isolations that are not alike

The lesson compares a container without a network and an internal network, and
shows the missing route. This course measures five limits: a published port
that does not open, the host that gets in anyway, the gateway that answers,
outside names, and two containers that share one network.

You work on the `essai-clos` network and `essai-*` containers. The challenge
uses `coffre`, `dehors`, `atelier-a` and `atelier-b`: do not touch them during
the course.

Related page: [Isolating a container from the network: none or an internal network](https://www.stephane-robert.info/en/docs/docker/isolate-a-container-from-the-network/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run reseau-interne
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

## 🚪 Exercise 1: a published port that does not open

Publish a port on a container of an internal network:

```bash
docker network create --internal --subnet 10.89.1.0/24 essai-clos > /dev/null
repondeur --name essai-dedans --network essai-clos -p 127.0.0.1:18500:80 > /dev/null; echo "code: $?"
docker container inspect essai-dedans --format '{{json .HostConfig.PortBindings}}'
docker port essai-dedans | wc -l
nc -w 3 127.0.0.1 18500; echo "code: $?"
```

```text
code: 0
{"80/tcp":[{"HostIp":"127.0.0.1","HostPort":"18500"}]}
0
code: 1
```

Docker accepts the command without a word, keeps the request in `PortBindings`,
and opens nothing. `docker port` is empty and the connection fails. A
"published" service that does not answer may therefore come from an internal
network.

## 🏠 Exercise 2: the host gets in anyway

Reach the container from the host, by its address:

```bash
IP=$(docker container inspect essai-dedans --format '{{(index .NetworkSettings.Networks "essai-clos").IPAddress}}')
echo "$IP"
nc -w 3 "$IP" 80; echo "code: $?"
```

```text
10.89.1.2
ici fd9f0c2feb20
code: 0
```

The host carries the gateway of this network, so it is part of it. An internal
network prevents members from getting out. It does not hide them from the
machine that hosts them.

## 🌉 Exercise 3: the gateway answers, the routable address does not

Start a web server on the host and call it from the container, by both
addresses of the host:

```bash
mkdir -p ~/essai-web && echo "page de l'hôte" > ~/essai-web/index.html
python3 -m http.server 18510 --bind 0.0.0.0 --directory ~/essai-web > /dev/null 2>&1 &
sleep 1
docker exec essai-dedans wget -q -T 3 -O - http://10.89.1.1:18510/
docker exec essai-dedans wget -q -T 3 -O - "http://$HOTE:18510/"; echo "code: $?"
```

```text
page de l'hôte
wget: can't connect to remote host (10.10.120.11): Network unreachable
code: 1
```

Through the gateway, the container reaches the host's service. Through the
routable address, no route: `Network unreachable`. A host service that listens
on all interfaces can therefore still be reached from an internal network. This
is the gap to know.

## 🔤 Exercise 4: outside names, and the refusal of none

Ask for a public name, then try to plug a `none` container into this network:

```bash
docker exec essai-dedans nslookup example.org 2>&1 | grep -o 'SERVFAIL'
docker run -d --name essai-nu --network none "$IMAGE" sleep 600 > /dev/null
docker network connect essai-clos essai-nu; echo "code: $?"
```

```text
SERVFAIL
SERVFAIL
Error response from daemon: container cannot be connected to multiple networks with one of the networks in private (none) mode
code: 1
```

Outside names do not resolve either. And a container started without a network
cannot be given one afterwards: it must be recreated.

## 👥 Exercise 5: two containers, a single network

`--network container:<name>` puts a second container in the network of the
first:

```bash
docker run -d --name essai-voisin --network container:essai-dedans "$IMAGE" sleep 600 > /dev/null
docker exec essai-voisin nc -w 3 127.0.0.1 80
docker run --rm --network container:essai-dedans -p 18501:80 "$IMAGE" true 2>&1 | grep -o 'conflicting options.*'
```

```text
ici fd9f0c2feb20
conflicting options: port publishing and the container type network mode
```

Both share the same address and the same `127.0.0.1`. The second cannot publish
a port: the network belongs to the first. This setup gives a diagnostic tool to
a confined container without touching its network.

## 🧹 Cleanup

```bash
docker rm -f essai-voisin essai-nu essai-dedans > /dev/null
docker network rm essai-clos
pkill -f 'http.server 18510'
rm -r ~/essai-web
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-clos
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset reseau-interne
dsoxlab check reseau-interne
```

```text
╭───── Result: reseau-interne ──────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: one container without a network, and two
others that talk to each other without ever getting out.

```bash
dsoxlab run reseau-interne
dsoxlab challenge reseau-interne
```
