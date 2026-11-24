# A restart loop, and two outcomes

The lesson explains the restart policies and how to repair a loop. This course
adds five investigation moves: measure the pace of restarts, recognise a loop
without failure, isolate the logs of the last attempt, examine a container that
does not stay up, and cap the restarts without recreating it.

You work on `essai-boucle` and `essai-zero`. The challenge uses the `appli-*`
containers: do not touch them during the course.

Related page: [Read a Docker startup failure: exit codes and loops](https://www.stephane-robert.info/en/docs/docker/read-a-startup-failure/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run troubleshoot-boucle-de-redemarrage
```

You are connected to `docker.lab`, where the engine runs. Start two containers
that loop. The `attendre` function waits until a container is between two
attempts. **Keep the same terminal until the cleanup.**

```bash
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
DEBUT=$(date +%s)
docker run -d --name essai-boucle --restart always "$IMAGE" sh -c 'echo "essai $(date +%T)"; echo reste > /trace.txt; exit 1' > /dev/null
docker run -d --name essai-zero --restart always "$IMAGE" sh -c 'echo tache finie; exit 0' > /dev/null
attendre() { until [ "$(docker container inspect "$1" --format '{{.State.Restarting}}')" = true ]; do sleep 0.2; done; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026. The times and the numbers of attempts will differ.

## ⏱️ Exercise 1: measure the pace of restarts

Each end of the program produces a `die` event. Compute the gap in seconds
between two ends:

```bash
sleep 12
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-boucle --filter event=die --format '{{.Time}}' | awk 'NR>1 {printf "%d ", $1-avant} {avant=$1} END {print ""}'
docker container inspect essai-boucle --format 'relances={{.RestartCount}}'
```

```text
0 0 1 1 1 4
relances=7
```

The gaps grow: Docker waits longer and longer. This trace is also useful
afterwards, to date the start of a loop.

## 0️⃣ Exercise 2: a loop without failure

The second container loops too. Look at its code:

```bash
attendre essai-zero
docker ps -a --filter name=essai-zero --format '{{.Names}} {{.Status}}'
docker logs --tail 1 essai-zero
```

```text
essai-zero Restarting (0) 4 seconds ago
tache finie
```

`Restarting (0)`: the program succeeds and ends, and the `always` policy starts
it again. There is nothing to repair in the program. The policy does not suit a
task that has an end.

## 📜 Exercise 3: the logs of the last attempt

The logs of a looping container mix all the attempts. Count the lines, then keep
only the last one, dated:

```bash
docker logs essai-boucle | wc -l
docker logs --tail 1 --timestamps essai-boucle
```

```text
7
2026-11-24T09:55:15.063471586Z essai 09:55:15
```

`--timestamps` dates the line, in universal time. With `--since` and this date,
you isolate the lines of a single attempt when the program writes several.

## 🔬 Exercise 4: examine a container that does not stay up

You want to see the container's files, but it does not stay up:

```bash
attendre essai-boucle
docker exec essai-boucle cat /trace.txt
docker diff essai-boucle
docker commit essai-boucle essai-autopsie:1 > /dev/null
docker run --rm essai-autopsie:1 cat /trace.txt
```

```text
Error response from daemon: Container f4c438d058db0c8bd1f9d125719e029f3ecc29b1a0423c5e7a5b6776dd617d78 is restarting, wait until the container is running
A /trace.txt
reste
```

`docker exec` is refused between two attempts. `docker diff` still lists what the
program wrote. `docker commit` freezes the container's files in an image, which
you open with another command. The original container keeps looping, untouched.

## 🛑 Exercise 5: cap without recreating

`docker update` changes the policy of an existing container. Give both a cap,
wait, then start `essai-boucle` again:

```bash
docker update --restart on-failure:2 essai-zero essai-boucle
sleep 20
docker ps -a --filter name=^essai- --format '{{.Names}} {{.Status}}'
docker start essai-boucle > /dev/null
sleep 6
docker container inspect essai-boucle --format 'relances={{.RestartCount}} statut={{.State.Status}} code={{.State.ExitCode}}'
```

```text
essai-zero
essai-boucle
essai-zero Exited (0) 19 seconds ago
essai-boucle Exited (1) 19 seconds ago
relances=2 statut=exited code=1
```

Both stopped, for two reasons: `essai-zero` returned 0, which `on-failure` does
not restart, and `essai-boucle` was already over its cap. After `docker start`,
the counter went back to zero and stopped at 2. The failure is still there: the
loop has ceased, nothing is repaired.

## 🧹 Cleanup

```bash
docker rm -f essai-boucle essai-zero > /dev/null
docker rmi essai-autopsie:1 > /dev/null
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset troubleshoot-boucle-de-redemarrage
dsoxlab check troubleshoot-boucle-de-redemarrage
```

```text
╭─ Result: troubleshoot-boucle-de-redemarrage ─╮
│  0 / 100 pts                                 │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests             │
╰──────────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: read two failing containers, remove their
cause, and let the engine restart the looping one without removing its policy.

```bash
dsoxlab run troubleshoot-boucle-de-redemarrage
dsoxlab challenge troubleshoot-boucle-de-redemarrage
```
