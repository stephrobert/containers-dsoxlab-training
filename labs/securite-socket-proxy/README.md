# Restrict a Docker API socket proxy

The lesson deploys a proxy and measures its profiles. This course looks at the
proxy from the tool's and the attacker's side: what is open without asking, a
Docker client that goes through it, what the events tell, a second network that
exposes it, and what its log keeps.

You work in `~/essai-filtre`, on `essai-relais`, `essai-cible` and `essai-*`
networks. The challenge uses `filtre-api`, `cible-1` and `cible-2`: do not
touch them during the course.

Related page: [Put a proxy in front of the Docker API](https://www.stephane-robert.info/en/docs/docker/put-a-proxy-in-front-of-the-docker-api/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-socket-proxy
```

You are connected to `docker.lab`, where the engine runs. `sert` starts the
proxy with a profile, `code` requests a path and returns the HTTP status.
**Keep the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-filtre && cd ~/essai-filtre
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
CURL=curlimages/curl:8.23.0@sha256:3fb7e13e5d179a845c97d78204f3f1064d1907037f26a3ebf91710571151fd93
PROXY=lscr.io/linuxserver/socket-proxy:3.4.7-r0-ls104@sha256:4e5e59efd3338205561c54262581992036e5a36ccca97d487b1d4ec41f9adc58
docker network create --internal essai-api > /dev/null
sert() { docker rm -f essai-relais > /dev/null 2>&1; docker run -d --name essai-relais --network essai-api --read-only --tmpfs /run -v /var/run/docker.sock:/var/run/docker.sock:ro "$@" "$PROXY" > /dev/null; sleep 2; }
code() { docker run --rm --network essai-api "$CURL" -s -m 4 -o /dev/null -w '%{http_code}' "http://essai-relais:2375/$1"; echo " $1"; }
docker run -d --init --name essai-cible -e CLE=demo --label equipe=paie "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🚪 Exercise 1: open without asking

Start the proxy without any variable, and try nine paths:

```bash
sert
for c in _ping version events info containers/json images/json volumes secrets system/df; do code $c; done
```

```text
200 _ping
200 version
200 events
403 info
403 containers/json
403 images/json
403 volumes
403 secrets
403 system/df
```

Three paths answer although you opened nothing. `events` is the least harmless
of the three, exercise 3 shows why. Make this list on your own proxy image:
defaults change from one project to another.

## 🧰 Exercise 2: a Docker client through the proxy

Open the containers, and point an ordinary Docker client at the proxy:

```bash
sert -e CONTAINERS=1
IP=$(docker inspect essai-relais --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
docker -H "tcp://$IP:2375" ps --format '{{.Names}}' | sort
docker -H "tcp://$IP:2375" images 2>&1 | grep -o '403 Forbidden'
docker -H "tcp://$IP:2375" run --rm "$IMAGE" true 2>&1 | grep -o '403 Forbidden'
docker -H "tcp://$IP:2375" logs essai-cible 2>&1 | grep -o '403 Forbidden'
```

```text
cible-1
cible-2
essai-cible
essai-relais
403 Forbidden
403 Forbidden
403 Forbidden
```

The client works as is for what is allowed, and shows the proxy's page for the
rest. `logs` is refused although the containers family is open: this image
handles some actions separately. So try every command of your tool.

## 📻 Exercise 3: what the events tell

Close everything, listen to the events through the proxy, and work normally on
the side:

```bash
sert
IP=$(docker inspect essai-relais --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
curl -s -m 5 "http://$IP:2375/events" > evenements.txt &
sleep 1
docker exec essai-cible sh -c 'echo mot-de-passe-tape > /dev/null'
wait
grep -o '"Action":"exec_create[^"]*"' evenements.txt | head -1
grep -o '"equipe":"paie"' evenements.txt | head -1
```

```text
"Action":"exec_create: sh -c echo mot-de-passe-tape \u003e /dev/null"
"equipe":"paie"
```

Without any family open, the tool sees the commands passed to `docker exec`,
with their arguments, and the containers' labels. A password typed in a command
is therefore broadcast. Close the events if the tool does not need them.

## 🕸️ Exercise 4: a second network that exposes it

Try to reach the proxy from another network, then connect it there:

```bash
docker network create --internal essai-autre > /dev/null
docker run --rm --network essai-autre "$CURL" -s -m 3 "http://$IP:2375/_ping"; echo "code: $?"
docker network connect essai-autre essai-relais
docker run --rm --network essai-autre "$CURL" -s -m 3 http://essai-relais:2375/_ping; echo " code: $?"
docker inspect essai-relais --format '{{range $n, $c := .NetworkSettings.Networks}}{{$n}} {{end}}'
```

```text
code: 7
OK code: 0
essai-api essai-autre
```

The proxy has no password: its network is its only protection. One more
connection, and all the containers of that network have the same rights as the
tool. Check the list of the proxy's networks, and that of its network's
containers.

## 📜 Exercise 5: what its log keeps

Cause a refusal, and read the proxy's log:

```bash
code containers/create > /dev/null
docker logs essai-relais 2>&1 | grep -oE '[0-9]{3} [0-9]+ - - [A-Z-]+ .*"GET /containers/create' | grep -oE '^403|PR--|GET .*' | xargs
docker logs essai-relais 2>&1 | grep -c '_ping'
```

```text
403 PR-- GET /containers/create
1
```

Each request is recorded with its status, and `PR--` marks a refusal by the
proxy itself. It is the only place where what a tool tried can be seen: the
daemon received nothing.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-relais essai-cible > /dev/null
docker network rm essai-api essai-autre > /dev/null
rm -rf ~/essai-filtre
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-socket-proxy
dsoxlab check securite-socket-proxy
```

```text
╭── Result: securite-socket-proxy ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/7 tests  │
╰───────────────────────────────────╯
```

0 out of 7: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a tool that reads and stops, and must be able
to do nothing else.

```bash
dsoxlab run securite-socket-proxy
dsoxlab challenge securite-socket-proxy
```
