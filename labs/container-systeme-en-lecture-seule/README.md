# Use a read-only container root filesystem

The lesson lists a service's writes, freezes its root and bounds its tmpfs
mounts. This course looks at what read-only lets through and what it breaks
without saying so: places that are still writable, a bypassed `noexec`, a tmpfs
that hides files, a tmpfs full of empty files, and a write lost silently.

You work on `essai-*` containers. The challenge uses the `worker` of its
project: do not touch it during the course.

Related page: [Read-only root filesystem, and a shutdown without data loss](https://www.stephane-robert.info/en/docs/docker/use-a-read-only-root-filesystem-and-stop-without-data-loss/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run container-systeme-en-lecture-seule
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-fige && cd ~/essai-fige
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
docker run -d --init --name essai-fige --read-only "$IMAGE" sleep 600 > /dev/null
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🗺️ Exercise 1: what stays writable

Try to write in seven directories, then in three files Docker prepares:

```bash
docker exec essai-fige sh -c 'for d in / /tmp /etc /sys /proc/sys/kernel /dev /dev/shm; do (echo x > $d/essai) 2>/dev/null && echo "$d : oui" || echo "$d : non"; done'
docker exec essai-fige sh -c 'for f in /etc/hosts /etc/resolv.conf /etc/hostname; do (echo "#" >> $f) 2>/dev/null && echo "$f : oui" || echo "$f : non"; done'
docker exec essai-fige sh -c 'mount' | grep -oE '/dev/shm type tmpfs .*size=[0-9]+k'
```

```text
/ : non
/tmp : non
/etc : non
/sys : non
/proc/sys/kernel : non
/dev : oui
/dev/shm : oui
/etc/hosts : non
/etc/resolv.conf : non
/etc/hostname : non
/dev/shm type tmpfs (rw,nosuid,nodev,noexec,relatime,size=65536k
```

`/dev` and `/dev/shm` stay open although you declared nothing. `/dev/shm`
offers 64 MiB, taken from the container's memory. The three network files are
frozen too: a program that rewrites `/etc/hosts` will fail.

## 📥 Exercise 2: tools that refuse too

Copy a file with `docker cp`, then try to remount the root for writing:

```bash
echo bonjour > note
docker cp -q note essai-fige:/dev/shm/note
docker exec essai-fige mount -o remount,rw / 2>&1
docker exec essai-fige touch /preuve
docker exec -i essai-fige sh -c 'cat > /dev/shm/note' < note; echo "code: $?"
```

```text
Error response from daemon: container rootfs is marked read-only
mount: permission denied (are you root?)
touch: /preuve: Read-only file system
code: 0
```

`docker cp` refuses everything, even towards a writable directory. To put a
file into a frozen container, go through its input, like the last line, or
through a mount planned at creation.

## 🎭 Exercise 3: a bypassed noexec

Put a script and a binary in a `noexec` tmpfs:

```bash
docker run --rm --read-only --tmpfs /espace:size=2m,noexec "$IMAGE" sh -c '
printf "echo execute\n" > /espace/s; chmod +x /espace/s; cp /bin/busybox /espace/b
/espace/s; echo "script direct: $?"
sh /espace/s; echo "par sh: $?"
/espace/b true; echo "binaire: $?"'
```

```text
script direct: 126
sh: /espace/s: Permission denied
execute
par sh: 0
sh: /espace/b: Permission denied
binaire: 126
```

The binary and the script are refused, but `sh` reads the script and runs it.
`noexec` hinders a dropped binary; it does not protect against an interpreter
present in the image. An image without a shell closes that door.

## 🫥 Exercise 4: a tmpfs that hides files

Count the files of an image directory, then mount a tmpfs on it, then a volume:

```bash
docker run --rm "$IMAGE" sh -c 'ls -A /etc/apk | wc -l'
docker run --rm --read-only --tmpfs /etc/apk "$IMAGE" sh -c 'ls -A /etc/apk | wc -l'
docker volume create essai-copie > /dev/null
docker run --rm --read-only -v essai-copie:/etc/apk "$IMAGE" sh -c 'ls -A /etc/apk | wc -l; touch /etc/apk/neuf && echo inscriptible'
docker volume rm essai-copie
```

```text
5
0
5
inscriptible
essai-copie
```

The tmpfs covers the directory and shows it empty. An empty volume first
receives a copy of the image's content. Mount a tmpfs on an empty directory, or
plan for the service to recreate what it expects.

## 🔢 Exercise 5: full, with empty files

Create empty files in a 4 MiB tmpfs limited to 20 entries:

```bash
docker run --rm --read-only --tmpfs /espace:size=4m,nr_inodes=20 "$IMAGE" sh -c '
for i in $(seq 30); do touch /espace/f$i 2>/dev/null; done
ls /espace | wc -l
touch /espace/encore
df -k /espace | tail -1
df -i /espace | tail -1'
```

```text
19
touch: /espace/encore: No space left on device
tmpfs                     4096         0      4096   0% /espace
tmpfs                       20        20         0 100% /espace
```

The message says space is missing, and `df -k` shows it is all there: the
entries are what is missing. In front of `No space left on device`, read both
`df`.

## 🤐 Exercise 6: a write lost silently

Run a program that ignores its errors, then another one that chooses its
temporary directory:

```bash
docker run --rm --read-only "$IMAGE" sh -c '(echo ligne > /var/log/app.log) 2>/dev/null; echo "travail fini"'; echo "code: $?"
docker run --rm --read-only "$IMAGE" mktemp; echo "code: $?"
docker run --rm --read-only -e TMPDIR=/dev/shm "$IMAGE" sh -c 'mktemp > /dev/null'; echo "code: $?"
```

```text
travail fini
code: 0
mktemp: : Read-only file system
code: 1
code: 0
```

The first returns 0 and wrote nothing: a running container does not prove that
the service works. Check the expected result. Many programs follow `TMPDIR`,
which avoids opening `/tmp`.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-fige > /dev/null
rm -rf ~/essai-fige
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset container-systeme-en-lecture-seule
dsoxlab check container-systeme-en-lecture-seule
```

```text
╭─ Result: container-systeme-en-lecture-seule ─╮
│  0 / 100 pts                                 │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests             │
╰──────────────────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a worker to freeze, which must keep giving
signs of life.

```bash
dsoxlab run container-systeme-en-lecture-seule
dsoxlab challenge container-systeme-en-lecture-seule
```
