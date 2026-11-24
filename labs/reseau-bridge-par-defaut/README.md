# The default network, and what it does not do

The lesson shows the address, the gateway and the absence of names on the
default network. This course adds five moves: an address that changes, what
this network refuses, a name set by hand, access to a service of the host, and
the host interface linked to a container.

You work on `essai-*` containers. The challenge uses `avant` and `arriere`: do
not touch them during the course.

Related page: [Default Docker network or your own: which to choose?](https://www.stephane-robert.info/en/docs/docker/default-network-or-your-own/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run reseau-bridge-par-defaut
```

You are connected to `docker.lab`, where the engine runs. The `repondeur`
function starts a container that answers one line on its port 80. **Keep the
same terminal until the cleanup**: the variables only exist in it.

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
HOTE=$(ip -o -4 route get 1.1.1.1 | awk '{for (i = 1; i <= NF; i++) if ($i == "src") print $(i + 1)}')
repondeur() { docker run -d "$@" "$IMAGE" sh -c 'exec nc -ll -p 80 -e echo "ici $(hostname)"'; }
docker version --format '{{.Server.Version}}'
adresse() { docker container inspect "$1" --format '{{.Name}} {{.NetworkSettings.Networks.bridge.IPAddress}}'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🔄 Exercise 1: an address that changes

Note the address of a container, stop it, start another one, then start the
first again:

```bash
repondeur --name essai-un > /dev/null
adresse essai-un
docker stop --timeout 1 essai-un > /dev/null
repondeur --name essai-deux > /dev/null
docker start essai-un > /dev/null
adresse essai-un
adresse essai-deux
```

```text
/essai-un 172.17.0.4
/essai-un 172.17.0.5
/essai-deux 172.17.0.4
```

`essai-deux` received the address `essai-un` had. A configuration that noted
this address would now reach another service, without any error. This is worse
than a failure: the connection succeeds.

## 🚫 Exercise 2: what this network refuses

Try to set an address, to give an alias, then to remove this network:

```bash
docker run --rm --ip 172.17.0.50 "$IMAGE" true 2>&1 | grep -i 'user'
docker run --rm --network-alias guichet "$IMAGE" true 2>&1 | grep -i 'user'
docker network rm bridge; echo "code: $?"
```

```text
user-specified IP address is supported on user-defined networks only
docker: network-scoped aliases are only supported for user-defined networks
Error response from daemon: bridge is a pre-defined network and cannot be removed
exit status 1
code: 1
```

All three requests are refused. A fixed address and an alias only exist on a
network you create, and the default network cannot be removed. These messages
are the most common reason to move to a dedicated network.

## 📒 Exercise 3: a name set by hand

Without a name service, `--add-host` writes a line in the container's
`/etc/hosts`:

```bash
IP=$(adresse essai-un | awk '{print $2}')
docker run -d --name essai-annuaire --add-host guichet:"$IP" "$IMAGE" sleep 600 > /dev/null
docker exec essai-annuaire grep guichet /etc/hosts
docker exec essai-annuaire nc -w 3 guichet 80
docker stop --timeout 1 essai-un > /dev/null
docker exec essai-annuaire nc -w 3 guichet 80; echo "code: $?"
```

```text
172.17.0.5	guichet
ici 76f360523345
code: 1
```

The name works as long as the address is right. The line is written when the
container is created and nobody updates it: it points to an address, not to a
container.

## 🖥️ Exercise 4: reach a service of the host

Start a web server on the host, then reach it from a container through the
gateway, which `host-gateway` points to for you:

```bash
mkdir -p ~/essai-web && echo "page de l'hôte" > ~/essai-web/index.html
python3 -m http.server 18420 --bind 0.0.0.0 --directory ~/essai-web > /dev/null 2>&1 &
sleep 1
docker run --rm --add-host hote:host-gateway "$IMAGE" sh -c 'grep -c hote /etc/hosts; wget -q -O - http://hote:18420/'
docker run --rm "$IMAGE" wget -q -T 3 -O - http://127.0.0.1:18420/; echo "code: $?"
```

```text
1
page de l'hôte
wget: can't connect to remote host (127.0.0.1): Connection refused
code: 1
```

The `127.0.0.1` of a container is its own, not the host's: the second attempt
fails. `host-gateway` avoids writing the address of the gateway by hand.

## 🔌 Exercise 5: the host interface linked to a container

Each container is linked to the bridge of its network by a virtual cable. Try
it on a separate network. The number read in the container points to the
interface on the host side:

```bash
docker network create --subnet 10.87.1.0/24 essai-pont > /dev/null
repondeur --name essai-cable --network essai-pont > /dev/null
N=$(docker exec essai-cable cat /sys/class/net/eth0/iflink)
ip -o link | grep "^$N:" | awk '{print $2}' | grep -o '^veth'
ip -o link | grep "^$N:" | grep -o 'master br-'
sudo iptables -t nat -S POSTROUTING | grep '10.87.1.0' | grep -oE '10.87.1.0/24|MASQUERADE'
```

```text
veth
master br-
10.87.1.0/24
MASQUERADE
```

The other end of the cable is a `veth` interface, attached to the bridge of the
network (`br-` followed by an identifier). The last lines come from the rule
that replaces the container's address with the host's when traffic leaves the
bridge. The default network follows the same setup, under another name.

## 🧹 Cleanup

```bash
docker rm -f essai-un essai-deux essai-annuaire essai-cable > /dev/null
docker network rm essai-pont
pkill -f 'http.server 18420'
rm -r ~/essai-web
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-pont
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset reseau-bridge-par-defaut
dsoxlab check reseau-bridge-par-defaut
```

```text
╭─ Result: reseau-bridge-par-defaut ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: map this network and get a token through a
real connection.

```bash
dsoxlab run reseau-bridge-par-defaut
dsoxlab challenge reseau-bridge-par-defaut
```
