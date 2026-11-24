# Correlate business requests and attribute CPU saturation

The lesson follows a request through the logs and reads the throttling
counters. This course adds five situations: two mixed streams, a message
written to a file, a bounded log, a log lost at recreation, and a slow service
nobody throttles.

You work in `~/essai-traces`, on an `essai-traces` project. The challenge uses
`/opt/dsoxlab-compose-correlation-et-saturation`: do not touch it during the
course.

Related page: [Read logs and attribute saturation](https://www.stephane-robert.info/en/docs/docker/read-logs-and-attribute-saturation/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-correlation-et-saturation
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a service that
talks in three places, and another one whose log is bounded. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-traces && cd ~/essai-traces
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  guichet:
    image: ${IMAGE}
    init: true
    command: ["sh", "-c", "echo demande recue; echo quantite invalide >&2; echo detail > /tmp/appli.log; sleep 600"]
  compteur:
    image: ${IMAGE}
    init: true
    command: ["sh", "-c", "for i in $$(seq 1 3000); do echo ligne $$i; done; sleep 600"]
    logging:
      driver: json-file
      options:
        max-size: "10k"
        max-file: "2"
EOF
docker compose up -d && sleep 3
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🔀 Exercise 1: two mixed streams

Read the log of `guichet`, then separate its two streams:

```bash
docker compose logs --no-log-prefix guichet 2> /dev/null
echo '-- sortie'
docker logs essai-traces-guichet-1 2> /dev/null
echo '-- erreur'
docker logs essai-traces-guichet-1 2>&1 > /dev/null
```

```text
demande recue
quantite invalide
-- sortie
demande recue
-- erreur
quantite invalide
```

`docker compose logs` prints everything on its standard output: redirecting
errors there removes nothing. `docker logs` returns the two streams separately.
To keep only the errors, use `docker logs`.

## 📁 Exercise 2: a message written to a file

Look for the word `detail` in the log, then point the file to the container's
output:

```bash
docker compose logs guichet | grep -c detail
docker compose exec guichet cat /tmp/appli.log
sed 's|echo detail|ln -s /dev/stdout /tmp/appli.log; echo detail|' compose.yaml > lien.yaml
docker compose -f lien.yaml up -d guichet && sleep 1
docker compose -f lien.yaml logs guichet | grep -c detail
```

```text
0
detail
1
```

Docker only collects the output and error of the main process. A file inside
escapes it, and grows in the write layer. The link to `/dev/stdout` is the
method several official images use.

## ✂️ Exercise 3: a bounded log

`compteur` wrote 3,000 lines. Count those that remain:

```bash
docker compose logs --no-log-prefix compteur | wc -l
docker compose logs --no-log-prefix compteur | sed -n '1p;$p'
```

```text
131
ligne 2870
ligne 3000
```

Two files of 10 KB at most only keep the end. The disk is protected, but an old
request is no longer there: choose the size according to how far back you want
to search.

## 🧹 Exercise 4: a lost log

Restart `guichet`, then recreate it, and count its messages each time:

```bash
docker compose restart guichet && sleep 1
docker compose logs guichet | grep -c 'demande recue'
docker compose up -d --force-recreate guichet && sleep 1
docker compose logs guichet | grep -c 'demande recue'
```

```text
2
1
```

A restart keeps the log, a recreation removes it with the container. Collect
the log of a failing service before recreating it.

## 🐌 Exercise 5: slow, and never throttled

Put three services on the same core, one capped, the other two free. The
`mesure` function keeps a service busy for three seconds:

```bash
cat > coeur.yaml <<'EOF'
x-base: &base
  image: ${IMAGE}
  init: true
  cpuset: "0"
  command: sleep 600
services:
  plafonne:
    <<: *base
    cpus: 0.2
  libre:
    <<: *base
  voisin:
    <<: *base
EOF
cat > mesure.sh <<'EOF'
bride() { awk '/nr_throttled/{print $2}' /sys/fs/cgroup/cpu.stat; }
attente() { awk -F'total=' '/some/{print $2}' /sys/fs/cgroup/cpu.pressure; }
b=$(bride); a=$(attente)
timeout 3 sh -c 'while :; do :; done'
echo "bride: $([ $(( $(bride) - b )) -gt 5 ] && echo oui || echo non), attente: $([ $(( $(attente) - a )) -gt 500000 ] && echo oui || echo non)"
EOF
docker compose -p essai-coeur -f coeur.yaml up -d
mesure() { docker compose -p essai-coeur -f coeur.yaml exec -T "$1" sh < mesure.sh 2> /dev/null | grep bride; }
mesure plafonne
mesure libre
docker compose -p essai-coeur -f coeur.yaml exec -d voisin timeout 6 sh -c 'while :; do :; done'
mesure libre
docker compose -p essai-coeur -f coeur.yaml down
```

```text
bride: oui, attente: oui
bride: non, attente: non
bride: non, attente: oui
```

The capped service is throttled and waits. The free service, alone, does not
wait. With a neighbour on the same core, it waits without being throttled:
`nr_throttled` only counts quotas. `cpu.pressure` measures the time spent
waiting for the CPU, whatever the cause. Read both before blaming a quota.

## 🧹 Cleanup

```bash
cd ~
docker compose -f ~/essai-traces/compose.yaml down
rm -r ~/essai-traces
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
dsoxlab reset compose-correlation-et-saturation
dsoxlab check compose-correlation-et-saturation
```

```text
╭─ Result: compose-correlation-et-saturation ─╮
│  0 / 100 pts                                │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests            │
╰─────────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two components, one request to follow, and a
single culprit to name.

```bash
dsoxlab run compose-correlation-et-saturation
dsoxlab challenge compose-correlation-et-saturation
```
