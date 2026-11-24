# Gate application startup on a successful migration

The lesson makes an application wait behind a migration. This course adds five
situations: two tasks in a chain, a task replayed at each start, a failure
bypassed without noticing, a lost exit code, and a task interrupted halfway.

You work in `~/essai-taches`, on an `essai-taches` project whose tasks write to
a log. The challenge uses the `dsoxlab-migration` project: do not touch it
during the course.

Related page: [Startup, readiness and health](https://www.stephane-robert.info/en/docs/docker/startup-readiness-and-health/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-tache-de-migration
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. The `CODE_UN`
variable will choose the exit code of the first task. **Keep the same terminal
until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-taches && cd ~/essai-taches
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
x-tache: &tache
  image: ${IMAGE}
  init: true
  environment:
    CODE_UN: ${CODE_UN:-0}
  volumes:
    - journal:/journal
services:
  un:
    <<: *tache
    command: ["sh", "-c", "echo un >> /journal/suivi; exit $$CODE_UN"]
  deux:
    <<: *tache
    command: ["sh", "-c", "echo deux >> /journal/suivi"]
    depends_on:
      un:
        condition: service_completed_successfully
  appli:
    <<: *tache
    command: ["sleep", "600"]
    depends_on:
      deux:
        condition: service_completed_successfully
volumes:
  journal:
EOF
etats() { docker compose ps -a --format '{{.Service}} {{.State}} {{.ExitCode}}' | sort; }
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## ⛓️ Exercise 1: two tasks in a chain

Start and read the order of the writes:

```bash
docker compose up -d
docker compose exec appli cat /journal/suivi
etats
```

```text
un
deux
appli running 0
deux exited 0
un exited 0
```

Each task waits for the successful end of the previous one, and `appli` waits
for the last. A finished task stays visible with `ps -a`, with its code.

## 🔁 Exercise 2: a task replayed at each start

Start again without changing the file:

```bash
AVANT=$(docker inspect essai-taches-appli-1 --format '{{.Id}}')
docker compose up -d
docker compose exec appli cat /journal/suivi
[ "$(docker inspect essai-taches-appli-1 --format '{{.Id}}')" = "$AVANT" ] && echo "appli: inchangee"
```

```text
un
deux
un
deux
appli: inchangee
```

Both tasks ran a second time, and `appli` did not move. A migration must
therefore tolerate being replayed at each deployment.

## 🕳️ Exercise 3: a bypassed failure

Make the first task fail, then start `appli` in three ways:

```bash
docker compose down -v
export CODE_UN=4
docker compose up -d 2>&1 | grep -o "didn't complete successfully.*"
etats
docker compose start appli 2>&1 | grep -o "didn't complete successfully.*"
docker compose up -d --no-deps appli; echo "code: $?"
etats
docker compose down -v
```

```text
didn't complete successfully: exit 4
appli created 0
deux created 0
un exited 4
didn't complete successfully: exit 4
code: 0
appli running 0
deux created 0
un exited 4
```

`up` and `start` refuse. `--no-deps` starts `appli` without looking at its
dependencies, without any warning: the application runs on a schema that was
not migrated. A `docker start` of the container would do the same. The
condition protects the normal path, not the shortcuts.

## 🔢 Exercise 4: a lost exit code

Run the failing task alone, in three ways, and read the returned code:

```bash
docker compose up -d un; echo "up -d: $?"
docker compose up --exit-code-from un un > /dev/null 2>&1; echo "exit-code-from: $?"
docker compose run --rm un > /dev/null 2>&1; echo "run: $?"
docker compose down -v
```

```text
up -d: 0
exit-code-from: 4
run: 4
```

`up -d` returns 0: it started the container, and does not wait for its end. In
a script, use `run --rm`, or `--exit-code-from`, which return the task's code.

## ✂️ Exercise 5: a task interrupted halfway

Two tasks write a result in two steps. Interrupt them in the middle:

```bash
cat > partiel.yaml <<'EOF'
x-tache: &tache
  image: ${IMAGE}
  init: true
  volumes:
    - resultat:/resultat
services:
  directe:
    <<: *tache
    command: ["sh", "-ec", "echo a > /resultat/direct; ${MILIEU:-true}; echo b >> /resultat/direct"]
  sure:
    <<: *tache
    command: ["sh", "-ec", "echo a > /resultat/sur.tmp; ${MILIEU:-true}; echo b >> /resultat/sur.tmp; mv /resultat/sur.tmp /resultat/sur"]
volumes:
  resultat:
EOF
MILIEU=false docker compose -f partiel.yaml run --rm directe > /dev/null 2>&1; echo "directe: $?"
MILIEU=false docker compose -f partiel.yaml run --rm sure > /dev/null 2>&1; echo "sure: $?"
docker compose -f partiel.yaml run --rm sure ls /resultat
docker compose -f partiel.yaml run --rm sure
docker compose -f partiel.yaml run --rm sure cat /resultat/sur
docker compose -f partiel.yaml down -v
```

```text
directe: 1
sure: 1
direct
sur.tmp
a
b
```

Both tasks fail, but the first one leaves an incomplete `direct` file the
application would take as good. The second works aside and renames at the end:
the result exists in full or not at all. A database gives the same guarantee
with a transaction.

## 🧹 Cleanup

```bash
cd ~
unset CODE_UN
rm -r ~/essai-taches
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
dsoxlab reset compose-tache-de-migration
dsoxlab check compose-tache-de-migration
```

```text
╭─ Result: compose-tache-de-migration ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests     │
╰──────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a real database, a migration to replay, and
an application that must wait for it.

```bash
dsoxlab run compose-tache-de-migration
dsoxlab challenge compose-tache-de-migration
```
