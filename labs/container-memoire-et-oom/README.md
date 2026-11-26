# Set a hard memory ceiling

The lesson sets a ceiling and proves an OOM by its counter. This course looks
at what follows: a ceiling written in Compose that does not apply, a full
memory that no process holds, a program killed because of another's appetite,
the trace left in the kernel's log, and a group that dies as a whole.

You work on `essai-*` containers. The challenge uses the `worker` service and
`/opt/dsoxlab-container-memoire-et-oom`: do not touch them during the course.

Related page: [Cap memory and the number of tasks of a container](https://www.stephane-robert.info/en/docs/docker/limit-memory-and-processes-of-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-memoire-et-oom
```

You are connected to `docker.lab`, where the engine runs. `cg` returns the
directory of a container's cgroup. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-memoire && cd ~/essai-memoire
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

## 📝 Exercise 1: a ceiling written, and not applied

Compose accepts two ways to write the memory ceiling. Try the second, change
it, and see which command takes it into account:

```bash
cat > compose.yaml <<EOF
services:
  app:
    image: $IMAGE
    container_name: essai-app
    network_mode: none
    init: true
    deploy: {resources: {limits: {memory: 40m}}}
    command: sleep 600
EOF
docker compose up -d 2> /dev/null; cat $(cg essai-app)/memory.max
sed -i 's/40m/48m/' compose.yaml
docker compose restart -t 1 2> /dev/null; cat $(cg essai-app)/memory.max
docker compose up -d 2> /dev/null; cat $(cg essai-app)/memory.max
sed -i 's/^    command/    mem_limit: 64m\n    command/' compose.yaml
docker compose up -d 2>&1 | grep -o "can't set distinct values.*"
cat $(cg essai-app)/memory.max
```

```text
41943040
41943040
50331648
can't set distinct values on 'mem_limit' and 'deploy.resources.limits.memory': invalid compose project
50331648
```

`restart` relaunches the existing container with its old settings. Only `up -d`
compares the file with the container and recreates it. The two ways do not mix:
two different values, and Compose refuses the whole project. Keep the one the
file already uses.

## 🫙 Exercise 2: a full memory nobody holds

Write 80 MiB into an in-memory filesystem, under a ceiling of 40, then try to
enter the container:

```bash
docker run -d --init --name essai-t --memory 40m --memory-swap 40m --tmpfs /t "$IMAGE" sleep 600 > /dev/null
docker exec essai-t dd if=/dev/zero of=/t/f bs=1M count=80; echo "rc=$?"
awk '/^(anon|shmem) / {print $1, int($2/1048576) " Mio"}' $(cg essai-t)/memory.stat
docker exec essai-t true 2>&1 | grep -o 'possibly OOM-killed'
docker update --memory 64m --memory-swap 64m essai-t > /dev/null
docker exec essai-t rm /t/f && awk '/^shmem / {print $1, $2}' $(cg essai-t)/memory.stat
docker run --rm --memory 40m --memory-swap 40m --tmpfs /t:size=20m "$IMAGE" dd if=/dev/zero of=/t/f bs=1M count=80 2>&1 | grep -o 'No space left on device'
```

```text
rc=137
anon 0 Mio
shmem 38 Mio
possibly OOM-killed
shmem 0
No space left on device
```

Killing `dd` freed nothing: the file stayed, and the `shmem` line shows it. Any
added command gets killed in turn. Raising the ceiling for as long as it takes
to delete the file unblocks the situation. To avoid it, give the mount a size:
the program then gets a write error, and nobody is killed.

## 🎯 Exercise 3: killed because of another's appetite

A first program occupies 32 MiB and asks for nothing more. A second asks for
30, under a ceiling of 60:

```bash
docker run -d --init --name essai-q --memory 60m --memory-swap 60m "$IMAGE" sleep 600 > /dev/null
docker exec -d essai-q awk 'BEGIN {s="x"; for(i=0;i<25;i++) s=s s; system("sleep 500")}'
sleep 3
docker exec essai-q ps -o args | grep -c '^awk'
docker exec essai-q dd if=/dev/zero of=/dev/null bs=30M count=1 2>&1 | grep -o '1+0 records out'
docker exec essai-q ps -o args | grep -c '^awk'
awk '/^oom_kill / {print}' $(cg essai-q)/memory.events
```

```text
1
1+0 records out
0
oom_kill 1
```

The requester succeeded, and it is the other that disappeared. The kernel first
kills the process that weighs the most, not the one that asked for the memory
in excess. When a program dies for no apparent reason, also look for who lives
next to it in the container.

## 📜 Exercise 4: the trace in the kernel's log

Find the previous incident in the machine's log:

```bash
ID=$(docker inspect -f '{{.Id}}' essai-q)
sudo dmesg | grep "oom-kill:" | grep "$ID" > trace
grep -oE 'constraint=[A-Z_]+' trace
grep -oE ',task=[^,]+' trace
grep -oE 'oom_memcg=[^,]+' trace | grep -c "$ID"
sudo dmesg | grep -A1 "oom-kill:.*$ID" | grep -oE 'Memory cgroup out of memory: Killed process'
sudo dmesg | grep -c 'constraint=CONSTRAINT_NONE'
```

```text
constraint=CONSTRAINT_MEMCG
,task=awk
1
Memory cgroup out of memory: Killed process
0
```

`CONSTRAINT_MEMCG` says a group's ceiling was hit, `oom_memcg` says which one,
and `task` names the victim. A memory shortage of the whole machine would read
`CONSTRAINT_NONE`: the last count is zero. This trace stays after the
container's death, whereas its cgroup is gone.

## ⛓️ Exercise 5: a group that dies as a whole

Ask the kernel not to choose, and cause the same incident:

```bash
docker run -d --name essai-g --memory 40m --memory-swap 40m "$IMAGE" sleep 600 > /dev/null
C=$(cg essai-g); cat $C/memory.oom.group
echo 1 | sudo tee $C/memory.oom.group > /dev/null
docker exec essai-g awk 'BEGIN {s="x"; for(i=0;i<26;i++) s=s s}'; echo "rc=$?"
sleep 1
docker inspect essai-g --format '{{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}'
docker run --help | grep -c 'oom-group'
```

```text
0
rc=137
exited 137 true
0
```

With `memory.oom.group` at 1, the whole group goes, first process included. It
is useful for a service whose processes make no sense without each other, and
the opposite of what is needed for a service that must survive. Docker has no
option for this setting and leaves it at zero.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
docker network ls --filter name=essai- -q | xargs -r docker network rm > /dev/null
rm -rf ~/essai-memoire
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c 'essai-\|15547'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-memoire-et-oom
dsoxlab check container-memoire-et-oom
```

```text
╭─ Result: container-memoire-et-oom ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a service to bring back within its budget,
and that must survive an OOM.

```bash
dsoxlab run container-memoire-et-oom
dsoxlab challenge container-memoire-et-oom
```
