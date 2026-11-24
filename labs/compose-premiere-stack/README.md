# Start and recreate a two-service Compose application

The lesson writes a first file, starts it and stops it. This course adds five
everyday situations: simulating before acting, running a one-off command,
multiplying a service, a restart that applies nothing, and a renamed service.

You work in `~/essai-duo`, on an `essai-duo` project. The challenge uses the
`dsoxlab-premiere-stack` project: do not touch it during the course.

Related page: [Describe an application with Compose: a first stack](https://www.stephane-robert.info/en/docs/docker/describe-an-application-with-compose/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-premiere-stack
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a file with two
services. **Keep the same terminal until the cleanup**: the variables only
exist in it.

```bash
mkdir -p ~/essai-duo && cd ~/essai-duo
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  calcul:
    image: ${IMAGE}
    init: true
    command: sleep 600
  vitrine:
    image: ${IMAGE}
    init: true
    command: sleep 600
    ports:
      - "127.0.0.1:18501:80"
EOF
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🧪 Exercise 1: simulate before acting

Ask Compose what it would do, then count the project's containers:

```bash
COMPOSE_PROGRESS=plain docker compose --dry-run up -d 2>&1 | grep -E 'Created|Started' | sort -u
docker compose ps -aq | wc -l
```

```text
 Container essai-duo-calcul-1 Created
 Container essai-duo-calcul-1 Started
 Container essai-duo-vitrine-1 Created
 Container essai-duo-vitrine-1 Started
 Network essai-duo_default Created
0
```

`--dry-run` announces each action and runs none of them. It completes `docker
compose config`, which shows the resolved file but not the actions to come.

## 🎯 Exercise 2: a one-off command

Start, then compare `exec` and `run` on the same service:

```bash
docker compose up -d
docker compose exec vitrine sh -c 'echo trace > /tmp/trace; cat /tmp/trace'
docker compose run --rm vitrine cat /tmp/trace
docker compose run --rm --service-ports vitrine true 2>&1 | grep -o 'port is already allocated'
docker compose ps -a --format '{{.Service}} {{.State}}'
```

```text
trace
cat: can't open '/tmp/trace': No such file or directory

port is already allocated
calcul running
vitrine running
```

`exec` enters the running container. `run` creates another one from the same
description: it does not see its neighbour's file. It does not publish the
service's ports, and asking it to fails here since the port is already taken.
`--rm` removes it at the end.

## 👯 Exercise 3: several containers for one service

Take `calcul` to three containers, count the addresses behind its name, then
try to double `vitrine`:

```bash
docker compose up -d --scale calcul=3
docker compose exec vitrine nslookup calcul 2>&1 | grep -c '^Address: *172'
docker compose up -d --scale calcul=3 --scale vitrine=2 2>&1 | grep -o 'port is already allocated'
docker compose ps -a --format '{{.Name}} {{.State}}' | sort
docker compose up -d
```

```text
3
port is already allocated
essai-duo-calcul-1 running
essai-duo-calcul-2 running
essai-duo-calcul-3 running
essai-duo-vitrine-1 running
essai-duo-vitrine-2 created
```

The name `calcul` designates three addresses. `vitrine` cannot be doubled: its
host port is fixed, and a single container can hold it. The second one stays in
the `created` state. The last `up -d` goes back to one container per service.

## 🔁 Exercise 4: a restart that applies nothing

Change `calcul`'s command in the file, restart it, then apply the file:

```bash
sed -i '/calcul:/,/command/s/sleep 600/sleep 601/' compose.yaml
docker compose restart calcul
docker compose ps --no-trunc --format '{{.Service}} {{.Command}}'
docker compose up -d
docker compose ps --no-trunc --format '{{.Service}} {{.Command}}'
```

```text
calcul "sleep 600"
vitrine "sleep 600"
calcul "sleep 601"
vitrine "sleep 600"
```

`restart` stops and starts the existing container again, without reading the
file. `up -d` compares the file with the container and recreates the one that
differs. After a change, `up -d` is what you need.

## 👻 Exercise 5: a renamed service

Rename `calcul` to `moteur` in the file, then start:

```bash
sed -i 's/^  calcul:/  moteur:/' compose.yaml
docker compose up -d 2>&1 | grep -o 'Found orphan containers ([^)]*)'
docker compose ps --format '{{.Service}}' | sort
docker compose up -d --remove-orphans
docker compose ps --format '{{.Service}}' | sort
```

```text
Found orphan containers (essai-duo-calcul-1)
calcul
moteur
vitrine
moteur
vitrine
```

For Compose, renaming a service means adding one: the old container keeps
running, described nowhere. It warns, and `--remove-orphans` removes what the
file no longer describes.

## 🧹 Cleanup

```bash
cd ~
docker compose -f ~/essai-duo/compose.yaml down
rm -r ~/essai-duo
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset compose-premiere-stack
dsoxlab check compose-premiere-stack
```

```text
╭─ Result: compose-premiere-stack ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two images ready, no file, and an application
to describe.

```bash
dsoxlab run compose-premiere-stack
dsoxlab challenge compose-premiere-stack
```
