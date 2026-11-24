# Wait for readiness, not just a running container

The lesson declares a probe and makes a service wait. This course looks at what
does not work: a condition without a probe, a probe that cannot run, a probe
that is too slow, waiting in a script, and a circular dependency.

You work in `~/essai-pouls`, on an `essai-pouls` project. The challenge uses
the `dsoxlab-health` project: do not touch it during the course.

Related page: [Startup, readiness and health](https://www.stephane-robert.info/en/docs/docker/startup-readiness-and-health/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-sante-et-dependances
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. The `sonde` function
prints the last result of the probe's log. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-pouls && cd ~/essai-pouls
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
  client:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on:
      base:
        condition: service_healthy
EOF
sonde() { docker inspect essai-pouls-base-1 --format '{{with index .State.Health.Log 0}}{{.ExitCode}} {{.Output}}{{end}}'; }
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## ❓ Exercise 1: a condition without a probe

`client` waits for `base` to be healthy, and `base` has no probe:

```bash
docker compose config -q; echo "code: $?"
docker compose up -d 2>&1 | grep -o 'has no healthcheck configured'
docker compose ps -a --format '{{.Service}} {{.State}}' | sort
docker compose down
```

```text
code: 0
has no healthcheck configured
base running
client created
```

The file is valid: the missing probe only shows at startup. `base` runs and
`client` stays in the `created` state.

## 🔧 Exercise 2: a probe that cannot run

Write a probe with a tool missing from the image, then a whole command in a
single `CMD` element:

```bash
cat > sonde.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
    healthcheck:
      test: ["CMD", "curl", "-f", "http://127.0.0.1"]
      interval: 1s
      retries: 2
EOF
docker compose -f sonde.yaml up -d && sleep 3
sonde | grep -o '^-1\|"curl": executable file not found'
sed -i 's|test: .*|test: ["CMD", "test -f /tmp/pret"]|' sonde.yaml
docker compose -f sonde.yaml up -d && sleep 3
sonde | grep -o '^-1\|stat test -f /tmp/pret: no such file or directory'
```

```text
-1
"curl": executable file not found
-1
stat test -f /tmp/pret: no such file or directory
```

Both probes return -1: the command was never run, and the application has
nothing to do with it. `CMD` expects one word per element. For a command
written in one block, you need `CMD-SHELL`, and a shell in the image. Always
read the probe's log before looking for a failure.

## 🐢 Exercise 3: a probe that is too slow

Give one second to a probe that needs five:

```bash
sed -i 's|test: .*|test: ["CMD-SHELL", "sleep 5"]|; s|retries: 2|retries: 1\n      timeout: 1s|' sonde.yaml
docker compose -f sonde.yaml up -d && sleep 4
sonde
docker compose -f sonde.yaml ps --format '{{.Health}}'
```

```text
-1 Health check exceeded timeout (1s)
unhealthy
```

The probe would have succeeded, but Docker stopped it first. The log says so:
`exceeded timeout`. A service that is slow under load can therefore become
`unhealthy` while it answers.

## ⏳ Exercise 4: waiting in a script

Probe a file, then ask `up` to wait, before and after creating it:

```bash
sed -i 's|test: .*|test: ["CMD-SHELL", "test -f /tmp/pret"]|' sonde.yaml
docker compose -f sonde.yaml up -d; echo "code: $?"
docker compose -f sonde.yaml up -d --wait 2>&1 | grep -o 'is unhealthy'
docker compose -f sonde.yaml exec base touch /tmp/pret && sleep 3
docker compose -f sonde.yaml up -d --wait; echo "code: $?"
docker compose -f sonde.yaml down
```

```text
code: 0
is unhealthy
code: 0
```

`up -d` returns 0 as soon as the container is started. `--wait` waits for the
`healthy` state and fails on `unhealthy`: it is the form to use in a deployment
script. `--wait-timeout` bounds the wait.

## 🔄 Exercise 5: a circular dependency

Make two services depend on each other, then tie a service to its dependency's
restarts:

```bash
cat > boucle.yaml <<'EOF'
services:
  a:
    image: ${IMAGE}
    depends_on: [b]
  b:
    image: ${IMAGE}
    depends_on: [a]
EOF
docker compose -f boucle.yaml config -q
cat > lien.yaml <<'EOF'
services:
  base:
    image: ${IMAGE}
    init: true
    command: sleep 600
  lie:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on:
      base:
        condition: service_started
        restart: true
  libre:
    image: ${IMAGE}
    init: true
    command: sleep 600
    depends_on: [base]
EOF
docker compose -f lien.yaml up -d
debut() { docker inspect "essai-pouls-$1-1" --format '{{.State.StartedAt}}'; }
LIE=$(debut lie); LIBRE=$(debut libre)
docker compose -f lien.yaml restart base
[ "$(debut lie)" = "$LIE" ] && echo "lie: inchange" || echo "lie: redemarre"
[ "$(debut libre)" = "$LIBRE" ] && echo "libre: inchange" || echo "libre: redemarre"
docker compose -f lien.yaml down
```

```text
dependency cycle detected: a -> b -> a
lie: redemarre
libre: inchange
```

Compose refuses the loop and gives its path. `restart: true` restarts `lie`
when Compose restarts `base`, and `libre` does not move. This holds for a
Compose command, not for a database that goes down by itself.

## 🧹 Cleanup

```bash
cd ~
rm -r ~/essai-pouls
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
dsoxlab reset compose-sante-et-dependances
dsoxlab check compose-sante-et-dependances
```

```text
╭─ Result: compose-sante-et-dependances ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests       │
╰────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a live server that is not ready yet, and a
client that tries only once.

```bash
dsoxlab run compose-sante-et-dependances
dsoxlab challenge compose-sante-et-dependances
```
