# Cgroups: what a container may consume

The lesson finds a container's cgroup and reads its ceilings there. This course
looks at what the kernel does with them: a full memory that is not, a ceiling
changed live, refused settings, a write made behind Docker's back, and a
ceiling common to several containers.

You work on `essai-*` containers and an `essai.slice` slice. The challenge uses
`mesure`, `libre` and `bride`: do not touch them during the course.

Related page: [Namespaces and cgroups: measure a container's isolation](https://www.stephane-robert.info/en/docs/docker/measure-container-isolation/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run internes-cgroups-v2
```

You are connected to `docker.lab`, where the engine runs. `cg` returns the
directory of a container's cgroup. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-cgroup && cd ~/essai-cgroup
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 💧 Exercise 1: a full memory that is not

Write a 200 MB file in a container capped at 64 MB, and look at what its memory
is made of:

```bash
docker run -d --init --name essai-m --memory 64m "$IMAGE" sleep 600 > /dev/null
C=$(cg essai-m)
docker exec essai-m dd if=/dev/zero of=/f bs=1M count=200 2>&1 | grep -o '200.0MB'
[ "$(cat $C/memory.current)" -gt 60000000 ] && echo 'memoire au plafond'
awk '/^(anon|file) / {print $1, int($2/1048576) " Mo"}' $C/memory.stat
awk '/^oom_kill / {print "tues : " $2}' $C/memory.events
[ "$(awk '/^max / {print $2}' $C/memory.events)" -gt 0 ] && echo 'plafond touche'
```

```text
200.0MB
memoire au plafond
anon 0 Mo
file 60 Mo
tues : 0
plafond touche
```

The container is at its ceiling and all is well: these pages come from the
written file, and the kernel gives them back when it needs to. The program's
memory is the `anon` line. A ceiling touched is not a breakdown; a non-zero
`oom_kill` line is one.

## 🎚️ Exercise 2: a ceiling changed live

Raise the ceiling, then lower it below what the container uses, without
restarting it:

```bash
cat $C/memory.max $C/memory.swap.max
docker update --memory 128m --memory-swap 128m essai-m > /dev/null
cat $C/memory.max $C/memory.swap.max
docker update --memory 8m --memory-swap 8m essai-m > /dev/null
cat $C/memory.max
[ "$(cat $C/memory.current)" -le 8388608 ] && echo 'le noyau a rendu les pages'
docker inspect essai-m --format '{{.State.Status}}, redemarrages : {{.RestartCount}}'
```

```text
67108864
67108864
134217728
0
8388608
le noyau a rendu les pages
running, redemarrages : 0
```

`memory.swap.max` only counts swap: at first, 64 MB of memory **and** 64 MB of
swap. When both options have the same value, swap is zero. The change is
immediate, and lowering the ceiling forces the kernel to take back the cache.

## 🚫 Exercise 3: refused settings

Ask for too little, ask for a contradiction, and read who refuses:

```bash
docker run --rm --memory 1m "$IMAGE" true 2>&1 | grep -o 'Minimum memory limit.*'
docker run --rm --memory 64m --memory-swap 32m "$IMAGE" true 2>&1 | grep -o 'Minimum memoryswap limit.*limit'
docker update --memory-reservation 4m essai-m 2>&1 | grep -o 'Minimum memory reservation.*'
docker update --memory 64m --memory-swap 64m essai-m > /dev/null
docker update --memory-reservation 16m essai-m > /dev/null
cat $C/memory.low
```

```text
Minimum memory limit allowed is 6MB
Minimum memoryswap limit should be larger than memory limit
Minimum memory reservation allowed is 6MB
16777216
```

It is the daemon that refuses, before the kernel is consulted. The last option
sets another file: `memory.low` is a share that the kernel avoids taking back
when the machine runs short of memory. It is not a ceiling.

## ✏️ Exercise 4: a write behind Docker's back

Change the ceiling in the file, compare with what Docker says, then restart:

```bash
sh -c "echo 33554432 > $C/memory.max" 2>&1 | grep -o 'Permission denied'
echo 33554432 | sudo tee $C/memory.max
docker inspect essai-m --format 'Docker croit : {{.HostConfig.Memory}}'
docker restart --timeout 1 essai-m > /dev/null
cat $C/memory.max
```

```text
Permission denied
33554432
Docker croit : 67108864
67108864
```

Reading is open to all, writing needs root. The kernel did apply the write and
Docker knew nothing of it: meanwhile, `docker inspect` was wrong. The restart
recreated the cgroup with Docker's value. Go through `docker update`, and check
in the file.

## 🗂️ Exercise 5: a ceiling for several containers

Create a systemd slice capped at 20 tasks, and put two containers in it:

```bash
printf '[Slice]\nTasksMax=20\n' | sudo tee /etc/systemd/system/essai.slice > /dev/null
sudo systemctl daemon-reload
for i in 1 2; do docker run -d --init --cgroup-parent essai.slice --name essai-s$i "$IMAGE" sleep 600 > /dev/null; done
T=/sys/fs/cgroup/essai.slice
ls -d $T/docker-* | wc -l; cat $T/pids.max
docker exec essai-s1 sh -c 'i=0; while [ $i -lt 30 ]; do sleep 15 & i=$((i+1)); done' 2>&1 | tail -1 | grep -o "can't fork"
docker exec essai-s2 true 2>&1 | grep -o 'Resource temporarily unavailable' | head -1
awk '/^max/ {print ($2 > 0) ? "la tranche a refuse" : "rien"}' $T/pids.events
awk '/^max/ {print "un conteneur : " $2}' $T/docker-*/pids.events
```

```text
2
20
can't fork
Resource temporarily unavailable
la tranche a refuse
un conteneur : 0
un conteneur : 0
```

The first container took everything, and it is the **second** that can no
longer start anything. The containers' counters say zero, because the refusal
comes from higher up: the tightest ceiling on the path wins. When a refusal
seems unexplainable, go up the parent directories.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
sudo systemctl stop essai.slice; sudo rm /etc/systemd/system/essai.slice; sudo systemctl daemon-reload
rm -rf ~/essai-cgroup
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset internes-cgroups-v2
dsoxlab check internes-cgroups-v2
```

```text
╭─── Result: internes-cgroups-v2 ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two containers to compare, and a third to cap
twice.

```bash
dsoxlab run internes-cgroups-v2
dsoxlab challenge internes-cgroups-v2
```
