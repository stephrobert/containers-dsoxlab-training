# Resolve Compose variables without mixing environments

The lesson separates the interpolation of the file and the environment of the
container. This course adds five moves: listing the expected variables, writing
a conditional value, reading a missing environment file, passing a dollar sign,
and a project name that changes by itself.

You work in `~/essai-valeurs`, on an `essai-valeurs` project. The challenge
uses `/opt/lab-compose-vars`: do not touch it during the course.

Related page: [Interpolation and environment files in Compose](https://www.stephane-robert.info/en/docs/docker/interpolation-and-environment-files/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-resolution-des-variables
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a file with one
service. **Keep the same terminal until the cleanup**: the variables only exist
in it.

```bash
mkdir -p ~/essai-valeurs && cd ~/essai-valeurs
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  app:
    image: ${IMAGE}
    init: true
    command: sleep 600
    environment:
      NIVEAU: ${NIVEAU:-normal}
      TRACE: ${DIAGNOSTIC:+active}
EOF
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 📋 Exercise 1: the expected variables

Ask for the list of variables the file expects:

```bash
docker compose config --variables | awk '{print $1, $2, $3}' | sort
```

```text
DIAGNOSTIC false active
IMAGE false
NAME REQUIRED DEFAULT
NIVEAU false normal
```

Each line gives the name, whether the variable is mandatory, and its default or
replacement value. It is the first thing to read in a `compose.yaml` you did
not write.

## 🎚️ Exercise 2: a conditional value

`${NAME:+text}` gives `text` when the variable is set, and nothing otherwise:

```bash
docker compose config | grep TRACE
DIAGNOSTIC=1 docker compose config | grep TRACE
DIAGNOSTIC= docker compose config | grep TRACE
```

```text
      TRACE: ""
      TRACE: active
      TRACE: ""
```

It is the opposite of `:-`. The value of `DIAGNOSTIC` never appears: only its
presence matters. An empty variable is the same here as a missing one.

## 📄 Exercise 3: a missing environment file

Add an environment file that does not exist, then make it optional:

```bash
cat >> compose.yaml <<'EOF'
    env_file:
      - path: ./poste.env
        required: true
EOF
docker compose config -q 2>&1 | grep -o 'poste.env not found'
sed -i 's/required: true/required: false/' compose.yaml
docker compose config -q; echo "code: $?"
```

```text
poste.env not found
code: 0
```

A missing `env_file` stops everything, except with `required: false`. Keep this
form for a file specific to each machine: for an essential file, the error is
better than an incomplete container.

## 💵 Exercise 4: a dollar sign in an environment file

Write a value that contains a dollar sign, read what the container receives,
then change the format:

```bash
echo 'CODE=ab$cd' > poste.env
docker compose run --rm app printenv CODE 2> /dev/null
sed -i 's/required: false/format: raw/' compose.yaml
docker compose run --rm app printenv CODE
docker compose run --rm -e CODE=ponctuel app printenv CODE
```

```text
ab
ab$cd
ponctuel
```

By default, Compose also expands the values of an `env_file`: `$cd`, not found,
became empty. `format: raw` passes the text as is. The `-e` option of `run`
comes before the file, for that command only.

## 🏷️ Exercise 5: a project name that changes by itself

Start, add a project name in `.env`, then look for your container:

```bash
docker compose up -d
echo 'COMPOSE_PROJECT_NAME=essai-autre' > .env
docker compose ps -q | wc -l
docker compose -p essai-valeurs ps --format '{{.Name}}'
COMPOSE_PROJECT_NAME=essai-shell docker compose config | head -1
docker compose -p essai-option config | head -1
```

```text
0
essai-valeurs-app-1
name: essai-shell
name: essai-option
```

The `.env` file also sets Compose itself. Here the container is still running,
but Compose looks at another project. `-p` comes before the shell variable,
which comes before `.env`. When an application seems gone, read the `name:`
line of `config`.

## 🧹 Cleanup

```bash
cd ~
docker compose -p essai-valeurs -f ~/essai-valeurs/compose.yaml down
rm -r ~/essai-valeurs
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
dsoxlab reset compose-resolution-des-variables
dsoxlab check compose-resolution-des-variables
```

```text
╭─ Result: compose-resolution-des-variables ─╮
│  0 / 100 pts                               │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests           │
╰────────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a confused declaration, three files of
values, and none to change.

```bash
dsoxlab run compose-resolution-des-variables
dsoxlab challenge compose-resolution-des-variables
```
