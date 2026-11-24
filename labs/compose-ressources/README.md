# Enforce Compose resource budgets on the engine

The lesson sets three limits and reads what the kernel applies. This course
adds five situations: a reservation that limits nothing, two notations that
contradict each other, values the engine refuses, a limit per container and not
per service, and the limits of a process.

You work in `~/essai-budget`, on an `essai-budget` project. The challenge uses
the `dsoxlab-ressources` project: do not touch it during the course.

Related page: [Limit resources and restarts of a Compose stack](https://www.stephane-robert.info/en/docs/docker/limit-resources-and-restarts-of-a-stack/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-ressources
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. The `noyau` function
prints cgroup settings, read in the container. **Keep the same terminal until
the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-budget && cd ~/essai-budget
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
noyau() { for f in "$@"; do printf '%s = ' "$f"; docker compose exec ouvrier cat "/sys/fs/cgroup/$f"; done; }
nproc
```

```text
5.6.1
2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🪑 Exercise 1: a reservation is not a limit

Give a service a memory reservation and a CPU weight:

```bash
cat > compose.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    mem_reservation: 24m
    cpu_shares: 256
EOF
docker compose up -d
noyau memory.low memory.max cpu.weight cpu.max
```

```text
memory.low = 25165824
memory.max = max
cpu.weight = 35
cpu.max = max 100000
```

`memory.max` and `cpu.max` are `max`: nothing is capped. The reservation
protects 24 MiB when memory runs short, and the weight arbitrates between
containers when the CPU is saturated. Alone, this service can take everything.

## ⚔️ Exercise 2: two notations that contradict each other

Write two different memory limits for the same service:

```bash
cat > double.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    mem_limit: 48m
    deploy:
      resources:
        limits:
          memory: 64M
EOF
docker compose -f double.yaml config -q
```

```text
services.ouvrier: can't set distinct values on 'mem_limit' and 'deploy.resources.limits.memory': invalid compose project
```

Compose refuses to choose. This happens quickly when a second file adds
`deploy` to a service already limited by the short form.

## 🙅 Exercise 3: values the engine refuses

Ask for more cores than the host has, a core that does not exist, then too
little memory:

```bash
cat > refus.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    cpus: "${PART:-0.2}"
    cpuset: "${COEURS:-0}"
    mem_limit: ${MEMOIRE:-32m}
EOF
PART=64 docker compose -f refus.yaml config -q; echo "code: $?"
PART=64 docker compose -f refus.yaml up -d
COEURS=63 docker compose -f refus.yaml up -d
MEMOIRE=2m docker compose -f refus.yaml up -d
docker compose -f refus.yaml up -d
docker compose exec ouvrier nproc
```

```text
code: 0
Error response from daemon: range of CPUs is from 0.01 to 2.00, as there are only 2 CPUs available
Error response from daemon: Requested CPUs are not available - requested 63, available: 0-1
Error response from daemon: Minimum memory limit allowed is 6MB
1
```

`config` accepts everything: only the engine knows the host, and it refuses at
creation. The same declaration can therefore start on one machine and fail on
another. The last try is valid, and `cpuset` leaves a single visible core.

## 👯 Exercise 4: a limit per container

Take the service to three containers and read each one's limit:

```bash
docker compose -f refus.yaml up -d --scale ouvrier=3
for i in 1 2 3; do docker inspect essai-budget-ouvrier-$i --format '{{.HostConfig.Memory}}'; done
docker compose -f refus.yaml stats --no-stream --format '{{.MemUsage}}' | cut -d/ -f2
docker compose -f refus.yaml up -d
```

```text
33554432
33554432
33554432
 32MiB
 32MiB
 32MiB
```

Each container is entitled to 32 MiB: the whole service can therefore take 96.
The limit is not shared, and multiplying a service multiplies its budget.

## 📏 Exercise 5: the limits of a process

Bound the size of files and the number of open files, then read the container's
memory peak:

```bash
cat > compose.yaml <<'EOF'
services:
  ouvrier:
    image: ${IMAGE}
    init: true
    command: sleep 600
    mem_limit: 40m
    ulimits:
      nofile: 32
      fsize: 1048576
EOF
docker compose up -d
docker compose exec ouvrier sh -c 'ulimit -n; dd if=/dev/zero of=/tmp/gros bs=1M count=3 2> /dev/null; echo "code: $?"; du -k /tmp/gros'
docker compose exec ouvrier dd if=/dev/zero of=/dev/null bs=20M count=2 2> /dev/null
docker compose exec ouvrier awk '{print ($1 > 20000000) ? "pic au-dela de 20 Mo" : "pic faible"}' /sys/fs/cgroup/memory.peak
```

```text
32
code: 153
1024	/tmp/gros
pic au-dela de 20 Mo
```

The kernel stops the process that exceeds 1 MiB in a file, with code 153 (128 +
25, SIGXFSZ): the container goes on. `ulimits` applies to each process, the
cgroup to the whole container. `memory.peak` keeps the highest value reached:
read it before choosing a limit.

## 🧹 Cleanup

```bash
cd ~
docker compose -f ~/essai-budget/compose.yaml down
rm -r ~/essai-budget
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
dsoxlab reset compose-ressources
dsoxlab check compose-ressources
```

```text
╭─── Result: compose-ressources ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three budgets to set, and to find again in
the kernel after a recreation.

```bash
dsoxlab run compose-ressources
dsoxlab challenge compose-ressources
```
