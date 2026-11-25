# Shared memory and descriptors

The lesson sets `/dev/shm` and descriptors at creation. This course shows what
breaks when they are badly set: files that can no longer be opened, a limit the
process raises itself, a full shared memory, a memory shared between
containers, and a container stuck by what it left there.

You work on `essai-*` containers, always with explicit values. The challenge
uses the `lab-ulimits:1.0` image and the `etroit` container, and asks you to
measure the default values: do not touch them during the course.

Related page: [Cap a container: CPU, ulimits and shared memory](https://www.stephane-robert.info/en/docs/docker/limit-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-ulimits-et-shm
```

You are connected to `docker.lab`, where the engine runs. `cg` returns the
directory of a container's cgroup. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-partage && cd ~/essai-partage
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📂 Exercise 1: files that can no longer be opened

Give a container 20 descriptors and have a single program open 40 files:

```bash
docker run -d --init --name essai-u --ulimit nofile=20:128 "$IMAGE" sleep 600 > /dev/null
docker exec essai-u sh -c 'mkdir /d; for i in $(seq 40); do echo $i > /d/$i; done'
docker exec essai-u sh -c 'timeout 2 tail -f /d/* 2>&1 > /dev/null | grep -o "No file descriptors available" | sort | uniq'
docker exec essai-u sh -c 'cat /d/* | wc -l'
```

```text
Terminated
No file descriptors available
40
```

`tail -f` keeps all its files open and hits the limit. `cat` opens them one by
one and gets through. The limit counts the files **open at the same time by one
process**, not the files that exist.

## 🪜 Exercise 2: the soft limit and the hard limit

Have the process raise the limit itself, then exceed the ceiling:

```bash
docker exec essai-u sh -c 'ulimit -n; ulimit -n 128 && ulimit -n; ulimit -n 200' 2>&1
docker exec essai-u sh -c 'ulimit -n'
sudo prlimit --pid $(pid essai-u) --nofile=100:128
sudo prlimit --pid $(pid essai-u) --nofile -o SOFT,HARD --noheadings
docker exec essai-u sh -c 'ulimit -n'
docker run --rm --ulimit nofile=64:32 "$IMAGE" true 2>&1 | grep -o 'soft limit must be.*'
docker update --ulimit nofile=100 essai-u 2>&1 | grep -o 'unknown flag: --ulimit'
```

```text
20
128
sh: error setting limit: Operation not permitted
20
100 128
20
soft limit must be less than or equal to hard limit: 64 > 32
unknown flag: --ulimit
```

A process can go up to its hard limit, no higher, even as root in the
container. Each process has its own: changing the first one's does not change
the next `docker exec`'s. And Docker cannot modify it live: one must recreate.

## 📦 Exercise 3: a full shared memory

Write more than the size of `/dev/shm`, then reserve without writing:

```bash
docker run -d --init --name essai-s --shm-size 16m --memory 256m "$IMAGE" sleep 600 > /dev/null
docker exec essai-s dd if=/dev/zero of=/dev/shm/f bs=1M count=20 2>&1 | grep -o 'No space left on device'
awk '/^shmem / {print int($2/1048576) " Mo comptes"}' $(cg essai-s)/memory.stat
docker exec essai-s rm /dev/shm/f
docker exec essai-s truncate -s 12M /dev/shm/vide
docker exec essai-s sh -c 'stat -c "%s octets annonces" /dev/shm/vide; du -m /dev/shm/vide'
awk '/^shmem / {print int($2/1048576) " Mo comptes"}' $(cg essai-s)/memory.stat
```

```text
No space left on device
16 Mo comptes
12582912 octets annonces
0	/dev/shm/vide
0 Mo comptes
```

“No space left on device” is not about the disk here: it is the shared memory
that is full, while the container still has plenty of memory. A file that is
only announced takes nothing: only written pages are counted.

## 🤝 Exercise 4: a memory shared between containers

Try to join a container's shared memory, then start again with a container that
allows it:

```bash
docker run --rm --ipc container:essai-s "$IMAGE" ls /dev/shm 2>&1 | grep -o 'non-shareable IPC'
docker run -d --init --name essai-i --ipc shareable --shm-size 32m "$IMAGE" sleep 600 > /dev/null
docker exec essai-i sh -c 'echo salut > /dev/shm/mot'
docker run --rm --ipc container:essai-i --shm-size 96m "$IMAGE" sh -c 'cat /dev/shm/mot; df -m /dev/shm | awk "END {print \$2 \" Mo\"}"'
docker run --rm --shm-size 32m "$IMAGE" ls -A /dev/shm | wc -l
```

```text
non-shareable IPC
salut
32 Mo
0
```

By default, shared memory is private. `--ipc shareable` opens a container's,
and another joins it with `--ipc container:`. The second asked for 96 MB in
vain: the size belongs to whoever created the space.

## 💥 Exercise 5: stuck by what it left

Give 64 MB of shared memory to a container that has only 32 MB of memory:

```bash
docker run -d --init --name essai-o --memory 32m --memory-swap 32m --shm-size 64m "$IMAGE" sleep 600 > /dev/null
docker exec essai-o dd if=/dev/zero of=/dev/shm/f bs=1M count=48 2> /dev/null; echo "code $?"
docker inspect essai-o --format '{{.State.Status}} tue={{.State.OOMKilled}}'
awk '/^(anon|shmem) / {print $1, int($2/1048576) " Mo"}' $(cg essai-o)/memory.stat
docker exec essai-o true > /dev/null 2>&1 || echo 'plus aucune commande possible'
docker restart --timeout 1 essai-o > /dev/null
docker exec essai-o ls -A /dev/shm | wc -l
```

```text
code 137
running tue=true
anon 0 Mo
shmem 30 Mo
plus aucune commande possible
0
```

The program is dead, its memory is returned, and yet about 30 MB remain: the
file is still in `/dev/shm`. The container runs but has no room left to start
anything, even to erase. The restart empties that memory. Always count the size
of `/dev/shm` in the memory limit.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-partage
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-ulimits-et-shm
dsoxlab check container-ulimits-et-shm
```

```text
╭─ Result: container-ulimits-et-shm ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two values to measure, two to set, and a
weighing.

```bash
dsoxlab run container-ulimits-et-shm
dsoxlab challenge container-ulimits-et-shm
```
