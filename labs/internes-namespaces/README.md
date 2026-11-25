# A namespace is a view, not a wall

The lesson compares a container's namespaces with the machine's. This course
uses them to work: one process with two numbers, two containers sharing a view,
the machine's tools in a container's network, a process list that lies, and a
namespace created without Docker.

You work on `essai-*` containers. The challenge uses `cloisonne` and
`indiscret`: do not touch them during the course.

Related page: [Namespaces and cgroups: measure a container's isolation](https://www.stephane-robert.info/en/docs/docker/measure-container-isolation/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run internes-namespaces
```

You are connected to `docker.lab`, where the engine runs. `pid` returns the
number, on the machine, of a container's first process. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-vue && cd ~/essai-vue
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
pid() { docker inspect -f '{{.State.Pid}}' "$1"; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔢 Exercise 1: one process, two numbers

Start a container, add a second process to it, and read what the kernel knows
about the latter:

```bash
docker run -d --init --name essai-a "$IMAGE" sleep 600 > /dev/null
docker exec -d essai-a sleep 601; sleep 1
P=$(pgrep -f '^sleep 601')
sudo awk '/NSpid/ {print NF-1 " numeros, le dernier est " $NF}' /proc/$P/status
docker exec essai-a pgrep -f '^sleep 601'
[ "$(sudo awk '/NSpid/ {print $2}' /proc/$P/status)" = "$P" ] && echo 'le premier est celui de la machine'
for n in pid mnt net; do [ "$(sudo readlink /proc/$P/ns/$n)" = "$(sudo readlink /proc/$(pid essai-a)/ns/$n)" ] && echo "$n : le meme que le processus principal"; done
```

```text
2 numeros, le dernier est 8
8
le premier est celui de la machine
pid : le meme que le processus principal
mnt : le meme que le processus principal
net : le meme que le processus principal
```

The `NSpid` line gives the two numbers of the same process, the machine's then
the container's. `docker exec` creates no new space: it enters the existing
ones.

## 👯 Exercise 2: two containers, a single view

Give a container another's view of processes, then its network:

```bash
docker run --rm --pid container:essai-a "$IMAGE" ps -o args | grep '^sleep'
docker run --rm --pid container:essai-a "$IMAGE" sh -c 'kill -9 $(pgrep -f "^sleep 601")'
docker exec essai-a pgrep -f '^sleep 601' || echo 'le voisin l a tue'
[ "$(docker run --rm --network container:essai-a "$IMAGE" hostname)" = "$(docker exec essai-a hostname)" ] && echo 'meme nom de machine'
docker run --rm --network container:essai-a "$IMAGE" sh -c 'ps -o args | grep -c "^sleep"'
```

```text
sleep 600
sleep 601
le voisin l a tue
meme nom de machine
0
```

Sharing processes also gives the power to kill them, if the user is the same.
Sharing the network does not share processes: the last count is zero. Each type
is shared separately.

## 🧰 Exercise 3: the machine's tools, the container's network

Enter only the container's network with `nsenter`:

```bash
sudo nsenter -t $(pid essai-a) -n ip -br link | awk '{sub(/@.*/, "", $1); print $1}'
sudo nsenter -t $(pid essai-a) -n hostname
sudo nsenter -t $(pid essai-a) -n -u hostname | wc -c
docker exec essai-a ss -tln 2>&1 | grep -o 'executable file not found'
sudo nsenter -t $(pid essai-a) -n ss -tln | wc -l
```

```text
lo
eth0
docker.lab
13
executable file not found
1
```

The `ss` command is not in the image. `nsenter -n` takes the machine's one and
makes it work in the container's network, without installing anything there.
The name shown remains `docker.lab` as long as one does not also enter the name
space, with `-u`: it is then 12 characters, plus a newline.

## 🪞 Exercise 4: a process list that lies

Enter the container's view of processes, without then with its files:

```bash
N=$(sudo nsenter -t $(pid essai-a) -p ps -e | wc -l)
[ "$N" -gt 50 ] && echo 'sans ses fichiers : toute la machine'
sudo nsenter -t $(pid essai-a) -p -m ps -o args
sudo nsenter -t $(pid essai-a) -p kill -0 $(pid essai-a) 2>&1 | grep -o 'No such process'
```

```text
sans ses fichiers : toute la machine
COMMAND
/sbin/docker-init -- sleep 600
sleep 600
ps -o args
No such process
```

`ps` asks nothing of the kernel: it reads `/proc`. In the first case, it is
still the machine's `/proc`, so the list is wrong. The last line proves it: the
number shown does not exist in that space. The mounts must be entered too, with
`-m`.

## 🛠️ Exercise 5: a namespace without Docker

Create spaces by hand, first a machine name, then a view of processes:

```bash
sudo unshare --uts sh -c 'hostname essai-nom; hostname'; hostname
sudo unshare --pid sh -c 'ls / > /dev/null; ls / > /dev/null' 2>&1 | grep -o 'Cannot fork'
sudo unshare --pid --fork --mount-proc sh -c 'echo "je suis $$"; ps -e -o comm= | sort | uniq | head -3'
touch garde
sudo unshare --uts="$PWD/garde" hostname essai-garde
sudo nsenter --uts="$PWD/garde" hostname
sudo umount garde
sudo nsenter --uts="$PWD/garde" hostname 2>&1 | grep -o 'Invalid argument'
```

```text
essai-nom
docker.lab
Cannot fork
je suis 1
head
ps
sh
essai-garde
Invalid argument
```

Docker does nothing more than these kernel calls. `Cannot fork` is the error to
know: in a view of processes, the first child becomes number 1, and when it
ends, nothing can be born there any more. `--fork` gives it a shell that lasts.
A space disappears with its last process, unless a file holds it.

## 🧹 Cleanup

```bash
cd ~
docker ps -aq --filter name=essai- | xargs docker rm -f > /dev/null
rm -rf ~/essai-vue
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset internes-namespaces
dsoxlab check internes-namespaces
```

```text
╭─── Result: internes-namespaces ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three identities to record, and a container
that looks at the others.

```bash
dsoxlab run internes-namespaces
dsoxlab challenge internes-namespaces
```
