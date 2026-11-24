# Where Docker stores a container's files

The lesson shows where the write layer is and what it holds. This course
measures what it costs: a removed file that frees nothing, a small change that
copies a big file, a sparse file, the space shared between containers, and a
limit that limits nothing.

You work in `~/essai-couches`, with the `essai-couches:1` image and `essai-*`
containers. The challenge uses `entrepot`: do not touch it during the course.

Related page: [Docker volumes: keep your data and mount files](https://www.stephane-robert.info/en/docs/docker/keep-data-and-mount-files/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run internes-stockage-des-images
```

You are connected to `docker.lab`, where the engine runs, and the Alpine image
is on the machine. Build a small image that holds a 20 MB file. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-couches && cd ~/essai-couches
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
printf 'FROM %s\nRUN head -c 20000000 /dev/urandom > /gros.bin\n' "$IMAGE" > Dockerfile
docker build -q -t essai-couches:1 . > /dev/null
taille() { docker container inspect --size "$1" --format '{{.SizeRw}}' | awk '{printf "%.1f Mo\n", $1/1000000}'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🗑️ Exercise 1: removing frees nothing

Remove the big file in a container:

```bash
docker run -d --name essai-supprime essai-couches:1 sleep 600 > /dev/null
docker exec essai-supprime rm /gros.bin
docker exec essai-supprime ls /gros.bin
docker diff essai-supprime
docker run --rm essai-couches:1 ls -s /gros.bin | awk '{print $2}'
```

```text
ls: /gros.bin: No such file or directory
D /gros.bin
/gros.bin
```

The container no longer sees the file (`D` in `docker diff`), but the image
still has it: another container reads it. Removing adds a mark in the write
layer, it takes nothing away below.

## 🐘 Exercise 2: one byte that costs twenty million

Compare the write layer before and after adding one byte to the big file:

```bash
docker run -d --name essai-copie essai-couches:1 sleep 600 > /dev/null
taille essai-copie
docker exec essai-copie sh -c 'printf x >> /gros.bin'
taille essai-copie
```

```text
0.0 Mo
20.0 Mo
```

To change a file of the image, the engine first copies it whole into the write
layer. Files that change often, such as a database, therefore belong in a
volume.

## 🕳️ Exercise 3: a sparse file

Create a 50 MB file without writing any byte, then another one by writing them:

```bash
docker run -d --name essai-creux essai-couches:1 sleep 600 > /dev/null
docker exec essai-creux truncate -s 50M /creux.bin
docker exec essai-creux sh -c 'ls -l /creux.bin | awk "{print \$5}"; du -k /creux.bin | cut -f1'
taille essai-creux
docker exec essai-creux dd if=/dev/zero of=/plein.bin bs=1M count=50 2> /dev/null
taille essai-creux
```

```text
52428800
0
0.0 Mo
52.4 Mo
```

`ls` shows the announced size, `du` the space taken. The first file takes
almost nothing, the second 50 MB. To look for what fills a disk, read `du`.

## 🤝 Exercise 4: three containers, one image

Start three containers of the same image and weigh their write layer:

```bash
for i in 1 2 3; do docker run -d --name essai-part$i essai-couches:1 sleep 600 > /dev/null; done
for i in 1 2 3; do taille essai-part$i; done
docker ps -s --filter name=essai-part1 --format '{{.Size}}'
```

```text
0.0 Mo
0.0 Mo
0.0 Mo
4.1kB (virtual 29.1MB)
```

Each container only costs its own layer. The `virtual` value adds the whole
image, shared by the three: do not add it up.

## 🚧 Exercise 5: a limit that limits nothing

Ask for a 10 MB write layer, write 30 MB to it, then give an absurd value. Then
set a bound another way:

```bash
docker run --rm --storage-opt size=10m "$IMAGE" sh -c 'dd if=/dev/zero of=/bloc bs=1M count=30 2> /dev/null; du -m /bloc'
docker run --rm --storage-opt size=abc "$IMAGE" true; echo "code: $?"
docker run --rm --read-only --tmpfs /travail:size=10m "$IMAGE" sh -c 'dd if=/dev/zero of=/travail/bloc bs=1M count=30 2>&1 | grep dd:; touch /marque'
```

```text
30	/bloc
code: 0
dd: error writing '/travail/bloc': No space left on device
touch: /marque: Read-only file system
```

On this engine, the option is accepted and has no effect: the 30 MB go through,
and `abc` raises no error. A code 0 therefore does not prove that a limit
applies, you have to try to exceed it. The read-only root and the tmpfs of a
set size really bound what the container writes.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-supprime essai-copie essai-creux essai-part1 essai-part2 essai-part3 > /dev/null
docker rmi essai-couches:1 > /dev/null
rm -r ~/essai-couches
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset internes-stockage-des-images
dsoxlab check internes-stockage-des-images
```

```text
╭─ Result: internes-stockage-des-images ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests       │
╰────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: find where a container's writes live, and
weigh them on the host's disk.

```bash
dsoxlab run internes-stockage-des-images
dsoxlab challenge internes-stockage-des-images
```
