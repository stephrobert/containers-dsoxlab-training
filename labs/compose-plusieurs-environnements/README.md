# Deploy isolated development and production Compose projects

The lesson transfers an artifact and separates two environments. This course
details the merging of two files, where mistakes are made: lists that add up, a
reversed order, a path that starts elsewhere, a project name that changes, and
a difference Compose does not see.

You work in `~/essai-fusion`, on `essai-*` projects. The challenge uses
`/opt/lab-compose-env` and the `dsoxlab-env-*` projects: do not touch them
during the course.

Related page: [Promote the same artifact between two environments](https://www.stephane-robert.info/en/docs/docker/promote-the-same-artifact-between-environments/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-plusieurs-environnements
```

You are connected to `docker.lab`, where the engine runs. `vue` displays the
merge of several files. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-fusion && cd ~/essai-fusion
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir conf && echo commun > conf/reglage
cat > base.yaml <<EOF
services:
  app:
    image: $IMAGE
    command: sleep 600
    init: true
    environment: {NIVEAU: base, COMMUN: oui}
    ports: ["127.0.0.1:18700:80"]
    dns: [192.0.2.1]
    volumes: ["donnees:/data", "./conf:/conf:ro"]
volumes:
  donnees:
EOF
vue() { docker compose -p essai-vue "$@" config; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## ➕ Exercise 1: lists that add up

Override the environment, the command, the ports and a mount, and read the
merge:

```bash
cat > test.yaml <<'EOF'
services:
  app:
    command: sleep 300
    environment: {NIVEAU: test}
    ports: ["127.0.0.1:18701:80"]
    dns: [192.0.2.2]
    volumes: ["autres:/data"]
volumes:
  autres:
EOF
docker compose -p essai-vue -f base.yaml -f test.yaml config --format json > vue.json
python3 -c 'import json; a = json.load(open("vue.json"))["services"]["app"]; print(a["command"], a["environment"]); print([p["published"] for p in a["ports"]], a["dns"]); print([(v["source"].split("/")[-1], v["target"]) for v in a["volumes"]])'
```

```text
['sleep', '300'] {'COMMUN': 'oui', 'NIVEAU': 'test'}
['18700', '18701'] ['192.0.2.1', '192.0.2.2']
[('autres', '/data'), ('conf', '/conf')]
```

The command is replaced, the environment is merged key by key, the ports and
DNS addresses add up. Mounts are compared by their destination: the `/data`
volume is replaced. Always read `config` before `up`.

## 🧽 Exercise 2: replacing or removing

Ask explicitly to replace a list, then to remove one:

```bash
cat > net.yaml <<'EOF'
services:
  app:
    ports: !override ["127.0.0.1:18702:80"]
    dns: !reset []
    environment:
      COMMUN: !reset null
EOF
docker compose -p essai-vue -f base.yaml -f net.yaml config --format json > vue.json
python3 -c 'import json; a = json.load(open("vue.json"))["services"]["app"]; print([p["published"] for p in a["ports"]], a.get("dns"), a["environment"])'
printf 'services:\n  app:\n    ports: []\n' > vide.yaml
docker compose -p essai-vue -f base.yaml -f vide.yaml config | grep published
```

```text
['18702'] None {'NIVEAU': 'base'}
        published: "18700"
```

An empty list removes nothing: it is added, so the base's port stays published.
To replace, `!override`; to remove, `!reset`.

## 🔃 Exercise 3: an order and a directory

Reverse the two files, then use them from another directory with a relative
path:

```bash
vue -f test.yaml -f base.yaml | grep NIVEAU
mkdir -p ailleurs/conf && echo surcharge > ailleurs/conf/reglage
printf 'services:\n  app:\n    volumes: ["./conf:/autre:ro"]\n' > ailleurs/plus.yaml
vue -f base.yaml -f ailleurs/plus.yaml | grep 'source: /' | sed "s#$HOME#~#; s/^ *//" | sort -u
vue -f ailleurs/plus.yaml -f base.yaml | grep 'source: /' | sed "s#$HOME#~#; s/^ *//" | sort -u
```

```text
      NIVEAU: base
source: ~/essai-fusion/conf
source: ~/essai-fusion/ailleurs/conf
```

The last file wins. And all relative paths start from the directory of the
**first** file, even those written in another directory: reversing the files
changes the mounted settings.

## 🪪 Exercise 4: a project name that changes

Start the same declaration under two names, write in one, then change the name
with a variable:

```bash
cat > seul.yaml <<EOF
services:
  app: {image: "$IMAGE", command: sleep 600, init: true, network_mode: none, volumes: ["donnees:/data"]}
volumes:
  donnees:
EOF
for p in essai-un essai-deux; do docker compose -p $p -f seul.yaml up -d > /dev/null 2>&1; done
docker compose -p essai-un -f seul.yaml exec -T app sh -c 'echo un > /data/v' < /dev/null
docker compose -p essai-deux -f seul.yaml exec -T app ls /data < /dev/null | wc -l
docker compose -p essai-un -f seul.yaml down > /dev/null 2>&1
COMPOSE_PROJECT_NAME=essai-deux docker compose -f seul.yaml ps --format '{{.Name}}'
docker compose -f seul.yaml ps -q | wc -l
docker volume ls -q | grep '^essai-'
```

```text
0
essai-deux-app-1
0
essai-deux_donnees
essai-un_donnees
```

The project name is part of each object's name: two projects do not see each
other. Without `-p`, Compose takes the variable, otherwise the directory's
name, and finds nothing. `down` left the volume: starting `essai-un` again will
find it.

## 🫥 Exercise 5: a difference Compose does not see

Change the value of a mounted file, then a variable, and ask Compose what
changes:

```bash
cat > suivi.yaml <<EOF
services:
  app: {image: "$IMAGE", command: sleep 600, init: true, network_mode: none, environment: {MODE: "\${MODE:-a}"}, volumes: ["./conf:/conf:ro"]}
EOF
monte() { docker compose -p essai-suivi -f suivi.yaml up -d 2>&1 | grep -oE 'Running|Recreated|Started' | tail -1; }
empreinte() { docker compose -p essai-suivi -f suivi.yaml config --hash app | cut -d' ' -f2 | cut -c1-8; }
monte; A=$(empreinte)
echo nouveau > conf/reglage; monte
[ "$A" = "$(empreinte)" ] && echo 'meme empreinte'
export MODE=b; monte
[ "$A" = "$(empreinte)" ] || echo 'autre empreinte'
unset MODE
```

```text
Started
Running
meme empreinte
Started
autre empreinte
```

Compose compares the declaration, not the content of the mounted files: the
service keeps its old setting in memory and nothing says so. A variable changes
the fingerprint and recreates the container. After changing a file, recreate
yourself.

## 🧹 Cleanup

```bash
cd ~
for p in essai-un essai-deux essai-suivi; do docker ps -aq --filter label=com.docker.compose.project=$p | xargs -r docker rm -f > /dev/null; done
docker volume ls -q | grep -E '^essai-(un|deux)_' | xargs -r docker volume rm > /dev/null
rm -rf ~/essai-fusion
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset compose-plusieurs-environnements
dsoxlab check compose-plusieurs-environnements
```

```text
╭─ Result: compose-plusieurs-environnements ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests           │
╰────────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: one image, two machines, and two environments
that do not mix.

```bash
dsoxlab run compose-plusieurs-environnements
dsoxlab challenge compose-plusieurs-environnements
```
