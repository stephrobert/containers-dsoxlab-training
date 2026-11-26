# Capping a processor, and proving it

The lesson sets `--cpus` and `--cpuset-cpus`, and reads the stop counter. This
course measures what happens next: when the limit bites, what the length of the
period costs, a weight that only matters under competition, a setting changed
live, and refused requests.

You work on `essai-*` containers. The challenge uses `brideur` and `epingle`:
do not touch them during the course. Percentages vary by a point or two from
one time to the next.

Related page: [Cap a container: CPU, ulimits and shared memory](https://www.stephane-robert.info/en/docs/docker/limit-a-container/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-limite-cpu
```

You are connected to `docker.lab`, where the engine runs. `boucles` starts a
busy container; `part` measures for three seconds the CPU it uses; `arrets`
reads its counter. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-cpu && cd ~/essai-cpu
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cg() { echo /sys/fs/cgroup/system.slice/docker-$(docker inspect -f '{{.Id}}' "$1").scope; }
boucles() { n=$1; c=$2; shift 2; docker run -d --init --name "$c" "$@" "$IMAGE" sh -c "for i in \$(seq $n); do while :; do :; done & done; wait" > /dev/null; sleep 1; }
temps() { awk '/^usage_usec/ {print $2}' $(cg "$1")/cpu.stat; }
part() { a=$(temps $1); sleep 3; b=$(temps $1); echo "$(( (b - a + 15000) / 30000 )) %"; }
arrets() { awk '/^nr_throttled/ {print $2}' $(cg "$1")/cpu.stat; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📉 Exercise 1: when the limit bites

Cross two limits and two loads:

```bash
for l in 0.5 1.5; do for n in 1 2; do
  boucles $n essai-x --cpus $l
  P=$(part essai-x); [ "$(arrets essai-x)" -gt 0 ] && M='retenu' || M='jamais retenu'
  echo "limite $l, $n boucle(s) : $P, $M"
  docker rm -f essai-x > /dev/null
done; done
```

```text
limite 0.5, 1 boucle(s) : 51 %, retenu
limite 0.5, 2 boucle(s) : 50 %, retenu
limite 1.5, 1 boucle(s) : 101 %, jamais retenu
limite 1.5, 2 boucle(s) : 151 %, retenu
```

A loop uses at most one CPU. It is enough to exceed 0.5, never to exceed 1.5.
The counter only moves if demand exceeds the limit: a counter at zero may mean
that the limit is wide, or that the load is too low to see it.

## ⏲️ Exercise 2: the length of the period

Give the same share over two periods, and measure how long a stop lasts:

```bash
for p in 10000 100000; do
  boucles 1 essai-x --cpu-period $p --cpu-quota $((p / 2))
  P=$(part essai-x)
  awk -v p=$p -v u="$P" '/^nr_throttled/ {n = $2} /^throttled_usec/ {t = $2} END {m = t / n / 1000; print "periode " p / 1000 " ms : " u ", arrets de " (m < 10 ? "moins de 10 ms" : "plus de 40 ms")}' $(cg essai-x)/cpu.stat
  docker rm -f essai-x > /dev/null
done
```

```text
periode 10 ms : 50 %, arrets de moins de 10 ms
periode 100 ms : 50 %, arrets de plus de 40 ms
```

The share is the same, the wait is not. With 100 ms, the default, a request
that comes at the wrong time waits nearly 50 ms. This is what gives stuttering
slowness on a service whose average is good.

## ⚖️ Exercise 3: a weight, not a ceiling

Make two containers compete on the same CPU with different weights, then remove
one:

```bash
boucles 1 essai-fort --cpuset-cpus 0 --cpu-shares 1024
boucles 1 essai-faible --cpuset-cpus 0 --cpu-shares 256
cat $(cg essai-fort)/cpu.weight $(cg essai-faible)/cpu.weight
for c in fort faible; do P=$(part essai-$c); V=${P% %}; [ "$V" -gt 50 ] && echo "$c : environ trois quarts" || echo "$c : environ un quart"; done
docker rm -f essai-fort > /dev/null
echo "faible, seul : $(part essai-faible)"
arrets essai-faible
```

```text
100
35
fort : environ trois quarts
faible : environ un quart
faible, seul : 101 %
0
```

The weight only serves to decide between them. Alone, the “weak” container
takes the whole CPU, and no stop is counted. The kernel does not take the value
as is: 1024 becomes 100, and 256 becomes 35.

## 🎛️ Exercise 4: a setting changed live

Cap the running container, try to lift the limit with zero, then with the
maximum:

```bash
C=$(cg essai-faible)
docker update --cpus 0.25 essai-faible > /dev/null
cat $C/cpu.max
docker update --cpus 0 essai-faible > /dev/null
cat $C/cpu.max
docker update --cpus 2 essai-faible > /dev/null
cat $C/cpu.max
docker inspect essai-faible --format '{{.State.Status}}, redemarrages : {{.RestartCount}}'
docker rm -f essai-faible > /dev/null
```

```text
25000 100000
25000 100000
200000 100000
running, redemarrages : 0
```

The change applies at once. But zero means “change nothing”, not “no limit”:
the command succeeds and the limit remains. Always read the file again after a
`docker update`.

## 🚫 Exercise 5: refused requests

Ask for more CPUs than the machine has, then two options that say the same
thing:

```bash
docker run --rm --cpus 8 "$IMAGE" true 2>&1 | grep -o 'range of CPUs.*'
docker run --rm --cpuset-cpus 5 "$IMAGE" true 2>&1 | grep -o 'Requested CPUs.*'
docker run --rm --cpus 0.5 --cpu-quota 50000 "$IMAGE" true 2>&1 | grep -o 'Conflicting options.*'
docker run --rm --cpu-period 10000 --cpu-quota 5000 "$IMAGE" cat /sys/fs/cgroup/cpu.max
```

```text
range of CPUs is from 0.01 to 2.00, as there are only 2 CPUs available
Requested CPUs are not available - requested 5, available: 0-1
Conflicting options: Nano CPUs and CPU Quota cannot both be set
5000 10000
```

The daemon compares the request with the machine. A file written for an
eight-CPU server may thus fail on a workstation that has two. `--cpus` is a
shortcut for the quota and period pair: one chooses one or the other.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs -r docker rm -f > /dev/null
rm -rf ~/essai-cpu
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-limite-cpu
dsoxlab check container-limite-cpu
```

```text
╭── Result: container-limite-cpu ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a slow container to understand, another to
pin, and a limit to prove.

```bash
dsoxlab run container-limite-cpu
dsoxlab challenge container-limite-cpu
```
