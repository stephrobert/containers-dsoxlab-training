# Where data survives: the three kinds of mount

The lesson presents the named volume, the bind mount, the tmpfs and read-only
mode. This course adds five situations: a mounted file that gets replaced, a
full tmpfs, a mount under another one, a volume that cannot be removed, and the
backup of a volume.

You work in `~/essai-montages`, on `essai-*` containers and volumes. The
challenge uses `archive` and `coffre-donnees`: do not touch them during the
course.

Related page: [Docker volumes: keep your data and mount files](https://www.stephane-robert.info/en/docs/docker/keep-data-and-mount-files/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run donnees-volumes-et-montages
```

You are connected to `docker.lab`, where the engine runs, and the Alpine image
is on the machine. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-montages && cd ~/essai-montages
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 📝 Exercise 1: a mounted file that gets replaced

Mount a single file, add a line to it, then replace it as many editors do:

```bash
echo 'port=8080' > reglages.conf
docker run -d --name essai-fichier --mount type=bind,source="$PWD/reglages.conf",target=/reglages.conf "$IMAGE" sleep 600 > /dev/null
echo 'mode=test' >> reglages.conf
docker exec essai-fichier cat /reglages.conf
echo 'port=9090' > nouveau.conf
mv nouveau.conf reglages.conf
cat reglages.conf
docker exec essai-fichier head -1 /reglages.conf
```

```text
port=8080
mode=test
port=9090
port=8080
```

The addition is visible, the replacement is not. Docker mounted the file
itself, not its name: after `mv`, the name points to another file, and the
container keeps the old one. Mount the directory when a file may be replaced.

## 🧯 Exercise 2: a full tmpfs

Give 4 MB to a space in memory and write 6 MB to it:

```bash
docker run -d --name essai-plein --mount type=tmpfs,target=/travail,tmpfs-size=4m "$IMAGE" sleep 600 > /dev/null
docker exec essai-plein dd if=/dev/zero of=/travail/bloc bs=1M count=6 2>&1 | grep dd:
docker exec essai-plein df -h /travail
docker container inspect essai-plein --format '{{.State.Status}}'
```

```text
dd: error writing '/travail/bloc': No space left on device
Filesystem                Size      Used Available Use% Mounted on
tmpfs                     4.0M      4.0M         0 100% /travail
running
```

`No space left on device` is not about the host's disk, but about the 4 MB of
the tmpfs. The container keeps running, and the space stays full until someone
removes the file. Without `tmpfs-size`, a tmpfs can take up to half of the
host's memory.

## 🪆 Exercise 3: a mount under another one

Give an in-memory cache inside a read-only directory, with then without the
mount point:

```bash
mkdir -p reference
docker run --rm -v "$PWD/reference:/ref:ro" --tmpfs /ref/cache "$IMAGE" true 2>&1 | grep -oE 'read-only file system' | head -1
mkdir reference/cache
docker run --rm -v "$PWD/reference:/ref:ro" --tmpfs /ref/cache "$IMAGE" sh -c 'echo ok > /ref/cache/a && cat /ref/cache/a; echo non > /ref/b'
```

```text
read-only file system
ok
sh: can't create /ref/b: Read-only file system
```

Docker has to create `/ref/cache` to mount something on it, and `/ref` is
read-only: the container does not start. When the directory already exists in
the source, both mounts live together, and each keeps its mode.

## 🔐 Exercise 4: a volume that cannot be removed

Stop a container that uses a volume, then try to remove the volume:

```bash
docker run -d --name essai-tenant -v essai-carnet:/donnees "$IMAGE" sleep 600 > /dev/null
docker stop --timeout 1 essai-tenant > /dev/null
docker volume rm essai-carnet 2>&1 | grep -o 'volume is in use'
docker ps --filter volume=essai-carnet --format '{{.Names}}' | wc -l
docker ps -a --filter volume=essai-carnet --format '{{.Names}} {{.Status}}' | cut -d' ' -f1,2
```

```text
volume is in use
0
essai-tenant Exited
```

A stopped container still holds its volume, and `docker ps` without `-a` does
not show it. The refusal protects the data: look for who holds it before
removing anything.

## 💾 Exercise 5: back up a volume and restore it

Archive a volume through a throwaway container that mounts it read-only, then
restore the archive into a new volume:

```bash
docker run --rm -v essai-carnet:/d "$IMAGE" sh -c 'echo ligne-1 > /d/carnet.txt; chown 4242 /d/carnet.txt'
docker run --rm -v essai-carnet:/d:ro -v "$PWD:/sauvegarde" "$IMAGE" tar -czf /sauvegarde/carnet.tgz -C /d .
docker run --rm -v essai-copie:/d -v "$PWD:/sauvegarde:ro" "$IMAGE" tar -xzf /sauvegarde/carnet.tgz -C /d
docker run --rm -v essai-copie:/d:ro "$IMAGE" sh -c 'cat /d/carnet.txt; stat -c %u /d/carnet.txt'
```

```text
ligne-1
4242
```

The content and the owner came back. The `:ro` mount guarantees that the backup
changes nothing. This method copies files: for a running database, use its own
backup tool.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-fichier essai-plein essai-tenant > /dev/null
docker volume rm essai-carnet essai-copie
sudo rm -r ~/essai-montages
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
essai-carnet
essai-copie
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset donnees-volumes-et-montages
dsoxlab check donnees-volumes-et-montages
```

```text
╭─ Result: donnees-volumes-et-montages ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: get a unique piece of data out of a container
before recreating it with the three mounts.

```bash
dsoxlab run donnees-volumes-et-montages
dsoxlab challenge donnees-volumes-et-montages
```
