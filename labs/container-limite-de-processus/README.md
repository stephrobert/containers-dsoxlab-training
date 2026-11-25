# Bound the container process count

The lesson sets a task ceiling and reads its refusal counter. This course deals
with choosing the value and its effects: where to write it, how many slots to
leave, what happens when it is lowered live, a health probe that fails because
of it, and a service that dies of a mere refusal.

You work on `essai-*` containers. The challenge uses the `worker` service and
`/opt/dsoxlab-container-limite-de-processus`: do not touch them during the
course. Every burst of the course is finite: do not launch any other.

Related page: [Cap memory and the number of tasks of a container](https://www.stephane-robert.info/en/docs/docker/limit-memory-and-processes-of-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-limite-de-processus
```

You are connected to `docker.lab`, where the engine runs. `cg` returns the
directory of a container's cgroup; `dormeurs` starts a finite number of `sleep`
there. **Keep the same terminal until the cleanup**: the variables only exist
in it.

```bash
mkdir -p ~/essai-taches && cd ~/essai-taches
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
dormeurs() { docker exec -d "$1" sh -c "i=0; while [ \$i -lt $2 ]; do sleep $3 & i=\$((i+1)); done; wait"; sleep 1; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📝 Exercise 1: where to write the value

Compose accepts two ways to write it. Mix them, keep one, then change it:

```bash
cat > compose.yaml <<EOF
services:
  app:
    image: $IMAGE
    container_name: essai-app
    network_mode: none
    init: true
    pids_limit: 30
    deploy: {resources: {limits: {pids: 12}}}
    command: sleep 600
EOF
docker compose up -d 2>&1 | grep -o "can't set distinct values.*"
sed -i '/pids_limit/d' compose.yaml
docker compose up -d 2> /dev/null; cat $(cg essai-app)/pids.max
sed -i 's/pids: 12/pids: 14/' compose.yaml
docker compose restart -t 1 2> /dev/null; cat $(cg essai-app)/pids.max
docker compose up -d -t 1 2> /dev/null; cat $(cg essai-app)/pids.max
```

```text
can't set distinct values on 'pids_limit' and 'deploy.resources.limits.pids': invalid compose project
12
12
14
```

Two different values for one setting, and Compose refuses everything. Then
`restart` keeps the old ceiling: only `up -d` rereads the file and recreates
the container. Always check in `pids.max`.

## 🪑 Exercise 2: how many slots to leave

Find from which ceiling one can still enter a container that does nothing, and
read the peak:

```bash
for n in 3 5 12; do
  docker run -d --name essai-n --pids-limit $n "$IMAGE" sleep 600 > /dev/null
  docker exec essai-n true > /dev/null 2>&1 && echo "$n : exec passe" || echo "$n : exec refuse"
  [ $n = 12 ] && [ "$(cat $(cg essai-n)/pids.peak)" -gt 4 ] && echo "au repos : $(cat $(cg essai-n)/pids.current), pointe : plus de 4"
  docker rm -f essai-n > /dev/null
done
```

```text
3 : exec refuse
5 : exec refuse
12 : exec passe
au repos : 1, pointe : plus de 4
```

A `docker exec` of a tiny command takes several slots for an instant, because
the tool that launches it uses some too. The count at rest does not show it;
`pids.peak` keeps the maximum reached. Set the ceiling on the measured peak,
with room for a diagnosis. The exact number depends on the machine: on ours,
between 6 and 7 the answer changes from one try to the next.

## 📉 Exercise 3: lowering below current use

Start six `sleep`, then lower the ceiling below what the container already
uses:

```bash
docker run -d --init --name essai-p "$IMAGE" sleep 600 > /dev/null
dormeurs essai-p 6 300
C=$(cg essai-p)
docker update --pids-limit 4 essai-p > /dev/null
echo "$(cat $C/pids.current) taches, plafond $(cat $C/pids.max)"
docker exec essai-p sh -c 'sleep 0 & wait' 2>&1 | grep -o "can't fork"
docker top essai-p -o pid,args | grep -cE '^[0-9]+ +sleep 300'
docker exec essai-p pkill -f 'sleep 300'; sleep 1
echo "$(cat $C/pids.current) taches"
docker update --pids-limit 20 essai-p > /dev/null
docker exec essai-p sh -c 'sleep 0 & wait' && echo 'de nouveau possible'
```

```text
9 taches, plafond 4
can't fork
6
2 taches
de nouveau possible
```

The ceiling refuses births, it kills nobody: the six `sleep` went on. `docker
top` reads from the machine and needs no slot. This behaviour differs from
memory, where lowering too far may kill.

## 🩺 Exercise 4: a health probe hit by the ceiling

Add a probe that always says yes, fill the container for twelve seconds, and
follow its state:

```bash
docker run -d --init --name essai-h --pids-limit 20 --health-cmd true --health-interval 2s --health-retries 2 "$IMAGE" sleep 600 > /dev/null
sleep 3; docker inspect essai-h --format '{{.State.Health.Status}}'
dormeurs essai-h 16 12
echo "$(cat $(cg essai-h)/pids.current) sur 20"
sleep 7; docker inspect essai-h --format '{{.State.Status}}, {{.State.Health.Status}}'
docker inspect essai-h --format '{{json .State.Health.Log}}' | grep -o 'Resource temporarily unavailable' | sort -u
sleep 10; docker inspect essai-h --format '{{.State.Status}}, {{.State.Health.Status}}'
```

```text
healthy
19 sur 20
running, unhealthy
Resource temporarily unavailable
running, healthy
```

The probe is a `docker exec`: without a slot, it fails, and a working service
is declared unhealthy. The health log gives the real cause. A tool that
restarts unhealthy containers would make the incident worse. One last trap
measured on this machine: at 20 tasks out of 20, `docker exec` went through, at
19 it failed; we have not established why. Rely on `pids.current` and
`pids.events`, not on `docker exec` alone.

## 💀 Exercise 5: dying of a mere refusal

Have the same burst carried by the container's first process, then by a child:

```bash
B='i=0; while [ $i -lt 40 ]; do sleep 2 & i=$((i+1)); done; wait'
docker run -d --name essai-fragile --pids-limit 12 "$IMAGE" sh -c "$B; sleep 600" > /dev/null
docker run -d --init --name essai-solide --pids-limit 12 "$IMAGE" sh -c "($B) || echo 'lot refuse, je continue'; sleep 600" > /dev/null
sleep 4
for c in essai-fragile essai-solide; do docker inspect $c --format '{{.Name}} {{.State.Status}} {{.State.ExitCode}} {{.State.OOMKilled}}'; docker logs $c 2>&1; done
```

```text
/essai-fragile exited 2 false
sh: can't fork: Resource temporarily unavailable
/essai-solide running 0 false
sh: can't fork: Resource temporarily unavailable
lot refuse, je continue
```

The kernel refused the same way in both cases. The first shell gives up on
refusal, and as it is the first process, everything stops with code 2. In the
second, it is a child that gives up. A ceiling only protects well a program
that can take a refusal.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
rm -rf ~/essai-taches
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
dsoxlab reset container-limite-de-processus
dsoxlab check container-limite-de-processus
```

```text
╭─ Result: container-limite-de-processus ─╮
│  0 / 100 pts                            │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests        │
╰─────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a service to bring back within its task
budget, and that must stay up.

```bash
dsoxlab run container-limite-de-processus
dsoxlab challenge container-limite-de-processus
```
