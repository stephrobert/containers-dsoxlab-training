# Repair one routed firewall path without dropping protections

The lesson probes a multi-hop flow and sets rules on the host. This course
builds a small router apart, and shows what misleads a diagnosis: a forgotten
return, a rule placed too far, two refusals that do not look alike, an already
established connection, and a half-wrong rules file.

You work in three network namespaces, `essai-c`, `essai-r` and `essai-s`: a
client, a router, a server. The machine's firewall is not touched. The
challenge uses the containers of its project: do not touch them during the
course.

Related page: [Diagnose Docker network and firewall issues](https://www.stephane-robert.info/en/docs/docker/diagnose-docker-network-and-firewall-issues/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run reseau-pare-feu-cible
```

You are connected to `docker.lab`, where the engine runs. `C`, `R` and `S` run
a command in each namespace, `va` requests a page from the client, `vide`
erases the router's rules. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-routes && cd ~/essai-routes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
for n in c r s; do sudo ip netns add essai-$n; done
C() { sudo ip netns exec essai-c "$@"; }; R() { sudo ip netns exec essai-r "$@"; }; S() { sudo ip netns exec essai-s "$@"; }
sudo ip link add ec type veth peer name erc && sudo ip link set ec netns essai-c && sudo ip link set erc netns essai-r
sudo ip link add es type veth peer name ers && sudo ip link set es netns essai-s && sudo ip link set ers netns essai-r
C ip addr add 10.77.1.10/24 dev ec; R ip addr add 10.77.1.1/24 dev erc
S ip addr add 10.77.2.10/24 dev es; R ip addr add 10.77.2.1/24 dev ers
C ip link set ec up; R ip link set erc up; S ip link set es up; R ip link set ers up
R sysctl -qw net.ipv4.ip_forward=1
C ip route add default via 10.77.1.1
mkdir page && echo bonjour > page/index.html
S python3 -m http.server 8080 --directory page > /dev/null 2>&1 &
sleep 1
va() { C curl -s -m 2 "http://10.77.2.10:${1:-8080}/"; echo "code: $?"; }
vide() { R iptables -F FORWARD; R iptables -P FORWARD ACCEPT; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## ↩️ Exercise 1: a forgotten return

Request the page, see where the request goes, then give the server a return
route:

```bash
va
C ip route get 10.77.2.10 | head -1 | grep -o 'via [0-9.]*'
S ip route get 10.77.1.10 2>&1
R iptables -A FORWARD -d 10.77.2.10 && va
R iptables -vnL FORWARD | awk 'NR==3{print ($1 > 0 ? "la demande est passee" : "rien n est passe")}'
vide
S ip route add 10.77.1.0/24 via 10.77.2.1
va
```

```text
code: 28
via 10.77.1.1
RTNETLINK answers: Network is unreachable
code: 28
la demande est passee
bonjour
code: 0
```

The router did forward the request: it is the server that did not know where to
answer. A rule without an action only counts, which makes it a probe without
effect. Check both directions before blaming a firewall.

## 🔢 Exercise 2: a rule placed too far

Refuse everything, then add the permission at the end, and read the counters:

```bash
R iptables -A FORWARD -j DROP
R iptables -A FORWARD -p tcp --dport 8080 -j ACCEPT
va
R iptables -vnL FORWARD | awk 'NR>2{print $3, ($1 > 0 ? "a servi" : "n a jamais servi")}'
R iptables -D FORWARD 2 && R iptables -I FORWARD 1 -p tcp --dport 8080 -j ACCEPT
va
R iptables -I FORWARD 2 -p tcp --sport 8080 -j ACCEPT
va
vide
```

```text
code: 28
DROP a servi
ACCEPT n a jamais servi
code: 28
bonjour
code: 0
```

Rules are read in order, and the first one that decides wins. A permission
whose counter is zero is a rule nothing reaches. Placed first, it lets the
request through; the answer still has to be let through.

## 🚧 Exercise 3: two refusals that do not look alike

Refuse in two ways, then target a port where nothing listens, and compare
`curl`'s codes:

```bash
R iptables -A FORWARD -p tcp --dport 8080 -j DROP; echo 'DROP'; va; vide
R iptables -A FORWARD -p tcp --dport 8080 -j REJECT --reject-with tcp-reset; echo 'REJECT'; va; vide
echo 'port ferme'; va 8099
S ss -ltnH 'sport = :8080' | awk '{print $4}'
```

```text
DROP
code: 28
REJECT
code: 7
port ferme
code: 7
*:8080
```

`DROP` makes one wait, code 28. `REJECT` answers at once, code 7, exactly like
a closed port. A "connection refused" therefore does not prove that the service
is stopped: look at what listens on the server.

## 🔗 Exercise 4: an already established connection

Open a long connection, then forbid new ones:

```bash
R iptables -P FORWARD DROP
R iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
R iptables -A FORWARD -p tcp --dport 8080 -m conntrack --ctstate NEW -j ACCEPT
va
cat > longue.py <<'EOF'
import socket, time
s = socket.create_connection(("10.77.2.10", 8080), 2)
time.sleep(3)
s.sendall(b"GET / HTTP/1.0\r\n\r\n")
d = b""
while (m := s.recv(999)):
    d += m
print("ancienne connexion :", d.split(b"\r\n\r\n")[1].decode().strip())
EOF
C python3 longue.py & P=$!
sleep 1; R iptables -D FORWARD 2; va; wait $P
```

```text
bonjour
code: 0
ancienne connexion : bonjour
code: 28
```

New requests are refused, and the old connection still receives its answer: the
rule for established connections lets it through. After a rule change, test
with a new connection, and do not forget those that last.

## 📄 Exercise 5: a half-wrong rules file

Load a file whose last line is wrong, then a correct file that loses the
policy:

```bash
R iptables-save -t filter > bon.txt
{ grep -v COMMIT bon.txt; echo '-A FORWARD -p tcp --dport 8080 -j ACCEPTE'; echo COMMIT; } > faux.txt
R iptables-restore < faux.txt 2> /dev/null; echo "code: $?"
R iptables-save -t filter | grep -v '^#' | sed 's/\[.*//' | cmp -s - <(grep -v '^#' bon.txt | sed 's/\[.*//') && echo 'regles inchangees'
vide; R iptables -S FORWARD
R iptables-restore < bon.txt && R iptables -S FORWARD
```

```text
code: 2
regles inchangees
-P FORWARD ACCEPT
-P FORWARD DROP
-A FORWARD -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

The file loads entirely or not at all: a wrong line leaves the earlier rules.
This is safer than a series of commands, which stops in the middle. Erasing the
rules, on the other hand, opens everything if the policy goes back to `ACCEPT`:
keep a backup before trying.

## 🧹 Cleanup

```bash
cd ~
sudo pkill -f '^python3 -m http.server 8080 --directory page'
for n in c r s; do sudo ip netns del essai-$n; done
ip netns list | grep -c essai
rm -rf ~/essai-routes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset reseau-pare-feu-cible
dsoxlab check reseau-pare-feu-cible
```

```text
╭── Result: reseau-pare-feu-cible ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests  │
╰───────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a flow to restore, and all the other doors to
keep closed.

```bash
dsoxlab run reseau-pare-feu-cible
dsoxlab challenge reseau-pare-feu-cible
```
