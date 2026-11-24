# Who is PID 1 decides whether your container stops or gets killed

The lesson shows why a PID 1 without a handler ignores SIGTERM, and how `exec`
or `--init` solve the problem. This course adds five moves: read in the kernel
whether a PID 1 handles SIGTERM, change the stop signal, send a signal without
stopping the container, relay the signal from a script that must stay in place,
and spot zombie processes.

You work in `~/essai-signaux`, on `essai-*` containers. The challenge uses
another application, in `/opt/lab-signaux`.

Related page: [Container lifecycle, PID 1 and clean shutdown in Docker](https://www.stephane-robert.info/en/docs/docker/container-lifecycle-and-signals/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-signaux-et-pid-1
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the `IMAGE` variable only exists in it.

```bash
mkdir -p ~/essai-signaux && cd ~/essai-signaux
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026.

## 🔬 Exercise 1: read whether PID 1 handles SIGTERM

Timing a stop requires stopping the container. The kernel gives the answer on a
running one: the `SigCgt` line of `/proc/1/status` is a mask of the signals the
process has a handler for. SIGTERM is number 15, hence bit 14, since bits are
counted from 0:

```bash
docker run -d --name essai-sourd "$IMAGE" sleep 600 > /dev/null
docker run -d --name essai-attentif "$IMAGE" sh -c 'trap "exit 0" TERM; while :; do sleep 1; done' > /dev/null
sleep 1
for c in essai-sourd essai-attentif; do
  M=$(docker exec $c awk '/^SigCgt/ {print $2}' /proc/1/status)
  echo "$c SigCgt=$M SIGTERM=$(( (0x$M >> 14) & 1 ))"
done
```

```text
essai-sourd SigCgt=0000000000000000 SIGTERM=0
essai-attentif SigCgt=0000000000014002 SIGTERM=1
```

`sleep` has no handler: its mask is zero, and it will ignore SIGTERM. The second
shell has bit 14 set to 1: it will handle it. You can now predict a ten-second
stop without causing it.

## 🎚️ Exercise 2: change the stop signal

Some applications stop on another signal than SIGTERM. This one only catches
SIGINT. Start it twice, the second time with `--stop-signal`:

```bash
docker run -d --name essai-int "$IMAGE" sh -c 'trap "echo int-recu; exit 0" INT; while :; do sleep 1; done' > /dev/null
docker run -d --name essai-int-regle --stop-signal SIGINT "$IMAGE" sh -c 'trap "echo int-recu; exit 0" INT; while :; do sleep 1; done' > /dev/null
sleep 1
for c in essai-int essai-int-regle; do
  docker stop --timeout 3 $c > /dev/null
  docker container inspect $c --format "$c StopSignal={{.Config.StopSignal}} code={{.State.ExitCode}}"
  docker logs $c
done
```

```text
essai-int StopSignal= code=137
essai-int-regle StopSignal=SIGINT code=0
int-recu
```

The first container received SIGTERM, ignored it and was killed: code 137, no
log. The second received SIGINT: it wrote its line and returned 0. So before
changing an application, check which signal it expects.

## 🔁 Exercise 3: a signal that does not stop

The word `kill` misleads: `docker kill` sends SIGKILL by default, but `--signal`
picks another one. Many services read their configuration again on SIGHUP. Send
it:

```bash
docker run -d --name essai-relecture "$IMAGE" sh -c 'trap "echo relecture" HUP; trap "exit 0" TERM; while :; do sleep 1; done' > /dev/null
sleep 1
docker kill --signal HUP essai-relecture
sleep 2
docker logs essai-relecture
docker container inspect essai-relecture --format 'etat={{.State.Status}}'
```

```text
essai-relecture
relecture
etat=running
```

The application handled the signal and the container still runs.

## 🤝 Exercise 4: relay the signal from a script

`exec` replaces the script with the application: nothing can run after it any
more. If the script must clean up at the end, it has to stay in place and relay
the signal itself:

```bash
cat > app.sh <<'EOF'
#!/bin/sh
trap 'echo app-recu; exit 0' TERM
echo app-demarre
while :; do sleep 1; done
EOF
cat > relais.sh <<'EOF'
#!/bin/sh
/relais/app.sh &
ENFANT=$!
trap "kill -TERM $ENFANT" TERM
wait $ENFANT
wait $ENFANT
CODE=$?
echo menage-fait
exit $CODE
EOF
chmod +x app.sh relais.sh
docker run -d --name essai-relais -v "$PWD:/relais:ro" "$IMAGE" /relais/relais.sh > /dev/null
sleep 1
docker exec essai-relais cat /proc/1/comm
docker stop essai-relais > /dev/null
docker container inspect essai-relais --format 'code={{.State.ExitCode}}'
docker logs essai-relais
```

```text
relais.sh
code=0
app-demarre
app-recu
menage-fait
```

PID 1 is still `relais.sh`. Its `trap` passed SIGTERM to the application, which
wrote `app-recu`, then the script ended with `menage-fait` and the code of the
application. Two `wait` are needed: the signal interrupts the first, and the
second waits for the real end. This setup does not suit the challenge, which
asks for the application itself to be PID 1.

## 🧟 Exercise 5: zombie processes

A finished process stays in the process table, in state `Z`, as long as its
parent has not read its exit code. When the parent disappears, PID 1 inherits
this work. Compare a PID 1 that does not do it with a container started with
`--init`:

```bash
docker run -d --name essai-zombies "$IMAGE" sh -c 'for i in 1 2 3; do (sleep 1 &); done; exec sleep 600' > /dev/null
docker run -d --init --name essai-init "$IMAGE" sh -c 'for i in 1 2 3; do (sleep 1 &); done; exec sleep 600' > /dev/null
sleep 3
docker exec essai-zombies ps -o pid,ppid,stat,comm
docker exec essai-init ps -o pid,ppid,stat,comm
```

```text
PID   PPID  STAT COMMAND
    1     0 S    sleep
    8     1 Z    sleep
   10     1 Z    sleep
   12     1 Z    sleep
   13     0 R    ps
PID   PPID  STAT COMMAND
    1     0 S    docker-init
    6     1 S    sleep
   13     0 R    ps
```

Without an init, three finished `sleep` stay in state `Z`, attached to PID 1.
With `docker-init`, they are gone. An application that starts many processes can
fill its process limit with zombies this way.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-sourd essai-attentif essai-int essai-int-regle essai-relecture essai-relais essai-zombies essai-init > /dev/null
rm -r ~/essai-signaux
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-signaux-et-pid-1
dsoxlab check container-signaux-et-pid-1
```

```text
╭─ Result: container-signaux-et-pid-1 ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: see a stop end in 137, then fix the image so
that the application receives the signal, without removing the preparation.

```bash
dsoxlab run container-signaux-et-pid-1
dsoxlab challenge container-signaux-et-pid-1
```
