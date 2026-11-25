# Recover space in a bounded ENOSPC sandbox

The lesson finds the full mount and frees the space without recreating. This
course shows five cases where the cause is mistaken: two mounts and one
message, an erased file that still takes space, a half-done write, a culprit
`ls` points at wrongly, and a space in memory that kills before being full.

You work on `essai-*` containers, with in-memory spaces of a few megabytes. The
challenge uses the `worker` of its project: do not touch it during the course.

Related page: [Rotate Docker logs and reclaim disk space](https://www.stephane-robert.info/en/docs/docker/rotate-docker-logs-and-reclaim-disk-space/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run troubleshoot-disque-plein
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-plein && cd ~/essai-plein
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
docker run -d --init --name essai-place --tmpfs /travail:size=4m --shm-size 2m "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🗺️ Exercise 1: two mounts, one message

Fill `/dev/shm`, and compare the state of the mounts:

```bash
docker exec essai-place dd if=/dev/zero of=/dev/shm/x bs=1M count=3 2>&1 | grep dd:
docker exec essai-place df -m /dev/shm /travail / | awk 'NR>1{print $6, $5}' | sed 's/^\/ .*/\/ (disque de l hote)/'
docker exec essai-place rm /dev/shm/x
```

```text
dd: error writing '/dev/shm/x': No space left on device
/dev/shm 100%
/travail 0%
/ (disque de l hote)
```

`No space left on device` does not say which space. Here, neither the host's
disk nor `/travail` is to blame: it is `/dev/shm`, whose size is set
separately. Always read `df` on the exact path that failed.

## 👻 Exercise 2: an erased file that still takes space

Erase a file a program keeps open:

```bash
docker exec essai-place dd if=/dev/zero of=/travail/a bs=1M count=3 2> /dev/null
docker exec -d essai-place sh -c 'exec 3< /travail/a; echo $$ > /tmp/pid; exec sleep 500'
sleep 1
docker exec essai-place rm /travail/a
docker exec essai-place sh -c 'du -sm /travail | cut -f1; df -m /travail | awk "NR==2{print \$3}"'
docker exec essai-place sh -c 'ls -l /proc/*/fd 2> /dev/null' | grep -o '/travail/a (deleted)'
docker exec essai-place sh -c 'kill $(cat /tmp/pid); sleep 1; df -m /travail | awk "NR==2{print \$3}"'
```

```text
0
3
/travail/a (deleted)
0
```

`du` no longer sees anything, `df` still counts 3 MB: the file has no name any
more, but a program still reads it. The gap between the two is the signal. The
space comes back when the program closes the file or stops.

## ✂️ Exercise 3: a half-done write

Write more than the space, then copy a small file:

```bash
docker exec essai-place sh -c 'yes ligne | head -c 6000000 > /travail/journal; echo "code: $?"' 2> /dev/null
docker exec essai-place stat -c '%s %n' /travail/journal
docker exec essai-place cp /etc/alpine-release /travail/copie; echo "code: $?"
docker exec essai-place stat -c '%s %n' /travail/copie
docker exec essai-place sh -c ': > /travail/journal; df -m /travail | awk "NR==2{print \$3}"'
```

```text
code: 1
4194304 /travail/journal
cp: write error: No space left on device
code: 1
0 /travail/copie
0
```

Both writes fail, and both leave a file: a cut log, an empty copy. A file that
exists is therefore not a file that was written. The last command empties the
log without erasing it, which frees the space even if a program keeps it open.

## 🕵️ Exercise 4: a culprit wrongly designated

Look for what takes the space, with `ls` then with `du`:

```bash
docker exec essai-place sh -c 'rm -f /travail/*; dd if=/dev/zero of=/travail/reel bs=1M count=2 2> /dev/null; truncate -s 100M /travail/creux'
docker exec essai-place ls -l /travail | awk 'NR>1{print $5, $9}'
docker exec essai-place sh -c 'du -k /travail/* | sort -n'
```

```text
104857600 creux
2097152 reel
0	/travail/creux
2048	/travail/reel
```

`ls` announces 100 MB for a file that takes none, in a space of 4 MB. Sort by
`du`: it is the only one that counts the blocks really taken.

## 💀 Exercise 5: a space in memory that kills

Give 100 MB of space to a container limited to 20 MB of memory, and write 60 of
them:

```bash
docker run -d --init --name essai-memoire --memory 20m --memory-swap 20m --tmpfs /travail:size=100m "$IMAGE" sleep 600 > /dev/null
docker exec essai-memoire dd if=/dev/zero of=/travail/x bs=1M count=60 > /dev/null 2>&1; echo "code: $?"
docker inspect essai-memoire --format '{{.State.Status}} OOMKilled={{.State.OOMKilled}}'
docker exec essai-memoire df /travail 2>&1 | grep -o 'possibly OOM-killed'
docker rm -f essai-memoire > /dev/null
```

```text
code: 137
running OOMKilled=true
possibly OOM-killed
```

A tmpfs is paid in memory: the write is killed well before the 100 MB, without
any disk-full message. The container still runs, but its memory is taken by the
file, and no command can be started in it any more. Choose a tmpfs size
together with the memory limit.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-place > /dev/null
rm -rf ~/essai-plein
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset troubleshoot-disque-plein
dsoxlab check troubleshoot-disque-plein
```

```text
╭─ Result: troubleshoot-disque-plein ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests    │
╰─────────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a full space, a receipt to keep, and a
container not to recreate.

```bash
dsoxlab run troubleshoot-disque-plein
dsoxlab challenge troubleshoot-disque-plein
```
