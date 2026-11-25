# Recover retained orphan data and remove only disposable data

The lesson finds a volume, backs it up and removes the right one. This course
shows the mistakes that damage or hide data: a label believed changed, a volume
held by a stopped container, a volume filled by an image, an unfaithful copy,
and a mistyped name.

You work on `essai-*` volumes. The challenge uses two
`dsoxlab-donnees-volume-orphelin-*` volumes: do not touch them during the
course.

Related page: [Find orphan Docker volumes without deleting everything](https://www.stephane-robert.info/en/docs/docker/recover-orphan-docker-volumes-without-losing-data/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run donnees-volume-orphelin
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-volumes && cd ~/essai-volumes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🏷️ Exercise 1: a label believed changed

Create a volume with a label, then create it again with another value:

```bash
docker volume create --label equipe=paie essai-a
docker volume create --label equipe=rh essai-a; echo "code: $?"
docker volume inspect essai-a --format '{{.Labels}}'
docker volume ls -q --filter label=equipe=rh | wc -l
```

```text
essai-a
essai-a
code: 0
map[equipe:paie]
0
```

The second creation succeeds and changes nothing: the volume existed. A label
is read in `inspect`, never in the command one typed. A cleanup filtered on
`equipe=rh` would not see this volume.

## ⚓ Exercise 2: a volume held by a stopped container

Attach the volume to a container that is not running, then look for orphans:

```bash
docker create --name essai-arrete -v essai-a:/d "$IMAGE" true > /dev/null
docker volume ls -q --filter dangling=true | grep -c '^essai-a$'
docker volume rm essai-a 2>&1 | grep -o 'volume is in use'
docker ps -a --filter volume=essai-a --format '{{.Names}} {{.State}}'
docker rm -v essai-arrete > /dev/null
docker volume ls -q --filter dangling=true | grep -c '^essai-a$'
```

```text
0
volume is in use
essai-arrete created
1
```

A created or stopped container counts as a reference. `docker ps -a --filter
volume=` says who holds the volume. And `docker rm -v` only removes unnamed
volumes: this one becomes an orphan.

## 🫗 Exercise 3: a volume filled by an image

Mount an empty volume on a filled image directory, writable, read-only, then
with `nocopy`:

```bash
compte() { docker run --rm -v "$1:/d:ro" "$IMAGE" sh -c 'ls -A /d | wc -l'; }
for m in rw ro nocopy; do
  docker volume create essai-$m > /dev/null
  docker run --rm -v essai-$m:/etc/apk:$m "$IMAGE" true
  echo "$m : $(compte essai-$m) fichiers"
done
```

```text
rw : 5 fichiers
ro : 5 fichiers
nocopy : 0 fichiers
```

Docker copies the image's content into an empty volume, **even mounted
read-only**. To examine a volume believed empty, mount it on a directory that
does not exist in the image, or add `nocopy`.

## 🧬 Exercise 4: an unfaithful copy

Copy a volume in two ways, and compare the owner then the content:

```bash
docker run --rm -v essai-a:/d "$IMAGE" sh -c 'mkdir /d/x; echo recu > /d/x/f; chown -R 1234:1234 /d/x'
docker volume create essai-b > /dev/null
C="docker run --rm -v essai-a:/s:ro -v essai-b:/d $IMAGE"
$C cp -r /s/. /d/
$C stat -c '%u' /d/x/f
$C cp -a /s/. /d/
$C stat -c '%u' /d/x/f
$C sh -c 'cd /s && find . -type f -exec sha256sum {} + > /tmp/s; cd /d && sha256sum -c /tmp/s'
```

```text
0
1234
./x/f: OK
```

`cp -r` gives everything to root, and a non-root service would no longer read
its data. `cp -a` keeps owners, permissions and dates. The last line compares
the contents: it is what allows one to speak of a copy.

## 🔤 Exercise 5: a mistyped name

Mount a volume whose name has one letter too many, then a subdirectory that
does not exist:

```bash
docker run --rm -v essai-aa:/d "$IMAGE" sh -c 'ls -A /d | wc -l'
docker volume ls -q | grep '^essai-a'
docker run --rm --mount type=volume,src=essai-a,dst=/d,volume-subpath=x "$IMAGE" ls /d
docker run --rm --mount type=volume,src=essai-a,dst=/d,volume-subpath=y "$IMAGE" ls /d 2>&1 | grep -o 'no such file or directory'
```

```text
0
essai-a
essai-aa
f
no such file or directory
```

The unknown name creates an empty volume, without a word: the service starts,
and its data seems lost. The unknown subdirectory stops the start. In front of
missing data, first check the mounted name.

## 🧹 Cleanup

```bash
cd ~
docker volume rm essai-a essai-aa essai-b essai-rw essai-ro essai-nocopy > /dev/null
rm -rf ~/essai-volumes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset donnees-volume-orphelin
dsoxlab check donnees-volume-orphelin
```

```text
╭─ Result: donnees-volume-orphelin ─╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: data to reconnect, and only one volume to
remove.

```bash
dsoxlab run donnees-volume-orphelin
dsoxlab challenge donnees-volume-orphelin
```
