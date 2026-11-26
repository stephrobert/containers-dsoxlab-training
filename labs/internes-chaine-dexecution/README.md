# Who really starts a container

The lesson climbs from your process up to the daemon. This course shows what
knowing that chain is for: knowing who refused a start, reading what was asked
of the kernel, understanding where a `docker exec` comes from, recognizing a
dead process nobody collects, and cutting a link.

You work on `essai-*` containers. The challenge uses `maillon` and
`maillon-bis`: do not touch them during the course, and do not restart the
daemon.

Related page: [Who launches a container: Docker's execution chain](https://www.stephane-robert.info/en/docs/docker/container-execution-chain/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run internes-chaine-dexecution
```

You are connected to `docker.lab`, where the engine runs. `pid` returns the
number, on the machine, of a container's first process; `parent` returns its
parent's. **Keep the same terminal until the cleanup**: the variables only
exist in it.

```bash
mkdir -p ~/essai-chaine && cd ~/essai-chaine
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
parent() { ps -o ppid= -p "$1" | tr -d ' '; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🙅 Exercise 1: who refused?

Cause four failures, and note for each whether the container was created:

```bash
docker run --name essai-e1 --runtime absent "$IMAGE" true 2>&1 | grep -o 'unknown or invalid runtime name'
docker run --name essai-e2 "$IMAGE" commande-absente 2>&1 | grep -oE 'failed to create shim task|runc create failed|executable file not found'
docker run --name essai-e3 -p 22:22 "$IMAGE" true 2>&1 | grep -oE 'failed to set up container networking|address already in use'
docker run --name essai-e4 -v relatif/x:/x "$IMAGE" true 2>&1 | grep -o 'invalid characters for a local volume name'
docker ps -a --filter name=essai-e --format '{{.Names}} {{.State}}' | sort
```

```text
unknown or invalid runtime name
failed to create shim task
runc create failed
executable file not found
failed to set up container networking
address already in use
invalid characters for a local volume name
essai-e2 created
essai-e3 created
```

The message names the floor. `OCI runtime create failed` comes from `runc`, at
the last moment; the others come from the daemon. In two cases, the container
exists in the `created` state and holds its name, because the failure came
after its creation.

## 📄 Exercise 2: what was asked of the kernel

Start a container and read the record `runc` received:

```bash
docker run -d --init --name essai-a --cpus 0.5 "$IMAGE" sleep 600 > /dev/null
ID=$(docker inspect -f '{{.Id}}' essai-a)
sudo cat /run/containerd/io.containerd.runtime.v2.task/moby/$ID/config.json > fiche.json
python3 -c 'import json; d = json.load(open("fiche.json")); print(d["process"]["args"]); print(len(d["process"]["capabilities"]["bounding"]), "capacites"); print(d["linux"]["resources"]["cpu"]["quota"])'
pgrep -c '^runc$'
sudo ctr -n moby tasks ls | grep -c "$ID"
```

```text
['/sbin/docker-init', '--', 'sleep', '600']
14 capacites
50000
0
1
```

Your options became a record: the command, the capabilities, the limits. `runc`
applied it then left, hence the zero. `ctr -n moby` shows the same container as
seen by containerd, without going through Docker.

## 🚪 Exercise 3: where a docker exec comes from

Add a process with `docker exec` and look at its parent, from outside then from
inside:

```bash
docker exec -d essai-a sleep 602; sleep 1
X=$(pgrep -f '^sleep 602')
[ "$(parent $X)" = "$(parent $(pid essai-a))" ] && echo 'meme parent que le processus principal'
[ "$(parent $X)" = "$(pid essai-a)" ] || echo 'il n est pas son enfant'
docker exec essai-a ps -o ppid,args | grep '[s]leep'
```

```text
meme parent que le processus principal
il n est pas son enfant
    0 /sbin/docker-init -- sleep 600
    1 sleep 600
    0 sleep 602
```

The added process is not the child of the first: it hangs from the same
intermediary, one notch above. From inside, its parent is 0, that is, out of
sight. This is why the first process does not know it and will not stop it
cleanly.

## 🧟 Exercise 4: a dead process nobody collects

Leave an orphan in a container without `--init`, then in one that has it:

```bash
docker run -d --name essai-sans "$IMAGE" sleep 600 > /dev/null
for c in essai-sans essai-a; do docker exec $c sh -c '(sleep 1 &) ; true'; done
sleep 2
for c in essai-sans essai-a; do echo "$c : $(docker exec $c ps -o ppid,stat,args | grep -c ' Z ') zombie"; done
docker exec essai-sans ps -o ppid,stat,args | grep ' Z '
docker exec essai-a ps -o pid,args | grep '^ *1 '
```

```text
essai-sans : 1 zombie
essai-a : 0 zombie
    1 Z    [sleep]
    1 /sbin/docker-init -- sleep 600
```

An orphan is handed to the container's number 1, and `sleep` cannot collect a
dead child: it stays in `Z` and takes up a slot. With `--init`, number 1 is a
small program that does so.

## ✂️ Exercise 5: cut a link

Kill one container's intermediary, then another's main process, from the
machine:

```bash
P=$(pid essai-sans)
sudo kill -9 $(parent $P); sleep 2
docker inspect essai-sans --format '{{.State.Status}} {{.State.ExitCode}}'
ps -o args= -p $P || echo 'processus disparu'
sudo kill -9 $(pid essai-a); sleep 1
docker inspect essai-a --format '{{.State.Status}} {{.State.ExitCode}}'
docker start essai-sans > /dev/null && docker inspect essai-sans --format '{{.State.Status}}'
```

```text
exited 137
processus disparu
exited 137
running
```

Both moves end the same as seen by Docker: `exited 137`. Without its
intermediary, the container is cleaned up by containerd. A 137 thus only says
“killed by signal 9”: not by whom, nor why. The other containers felt nothing,
and the container restarts.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-chaine
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset internes-chaine-dexecution
dsoxlab check internes-chaine-dexecution
```

```text
╭─ Result: internes-chaine-dexecution ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two containers, their intermediaries, and
three numbers to record.

```bash
dsoxlab run internes-chaine-dexecution
dsoxlab challenge internes-chaine-dexecution
```
