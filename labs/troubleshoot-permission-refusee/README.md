# Three refused accesses, three causes

The lesson separates three causes: the mount, the rights and the mode of the
file. This course makes you meet five refusals that look like them, and that
these three checks do not explain.

You work in `~/essai-refus`, on `essai-*` containers. The challenge uses
`perm-a`, `perm-b`, `perm-c` and `temoin-sans-bit`: do not touch them during
the course.

Related page: [Docker volume permissions: three common causes of an access denied](https://www.stephane-robert.info/en/docs/docker/volume-permissions/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run troubleshoot-permission-refusee
```

You are connected to `docker.lab`, where the engine runs, and the Alpine image
is on the machine. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-refus && cd ~/essai-refus
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🚪 Exercise 1: a closed parent directory

The file can be read by everyone, and it is refused:

```bash
mkdir -p coffre/dossier && echo bonjour > coffre/dossier/note && chmod 644 coffre/dossier/note && chmod 700 coffre
docker run --rm --user 4343 -v "$PWD/coffre:/coffre" "$IMAGE" cat /coffre/dossier/note
docker run --rm -v "$PWD/coffre:/coffre" "$IMAGE" stat -c '%a %n' /coffre /coffre/dossier /coffre/dossier/note
```

```text
cat: can't open '/coffre/dossier/note': Permission denied
700 /coffre
775 /coffre/dossier
644 /coffre/dossier/note
```

Every directory of the path must be traversable. The first, in 700, stops
everyone but its owner. Read the rights of each level, not only those of the
file.

## 🧱 Exercise 2: a read-only root

The message is the one of a read-only mount, and the container has no mount:

```bash
docker run -d --name essai-racine --read-only "$IMAGE" sleep 600 > /dev/null
docker exec essai-racine touch /marque
docker container inspect essai-racine --format '{{len .Mounts}} montage(s), ReadonlyRootfs={{.HostConfig.ReadonlyRootfs}}'
```

```text
touch: /marque: Read-only file system
0 montage(s), ReadonlyRootfs=true
```

`.Mounts` is empty: the question of the mount mode has no answer here. The root
itself refuses, through the `--read-only` option, visible in
`.HostConfig.ReadonlyRootfs`.

## ⛔ Exercise 3: a mount that forbids execution

The script is executable, and the execution is refused:

```bash
docker run -d --name essai-noexec --tmpfs /outils:noexec "$IMAGE" sleep 600 > /dev/null
docker exec essai-noexec sh -c 'printf "#!/bin/sh\necho lance\n" > /outils/o.sh; chmod 755 /outils/o.sh; stat -c %a /outils/o.sh; /outils/o.sh'
docker exec essai-noexec sh -c 'grep " /outils " /proc/mounts | grep -o noexec'
docker exec essai-noexec sh /outils/o.sh
```

```text
755
sh: /outils/o.sh: Permission denied
noexec
lance
```

The mode is right, the mount carries `noexec`. `/proc/mounts`, read in the
container, gives the real options. The last command succeeds, because `sh` runs
and reads the script.

## 👑 Exercise 4: root, and yet refused

Root usually reads every file. Take away the capability that allows it:

```bash
docker run --rm -v "$PWD/coffre:/coffre" "$IMAGE" cat /coffre/dossier/note
docker run --rm --cap-drop DAC_OVERRIDE --cap-drop DAC_READ_SEARCH -v "$PWD/coffre:/coffre" "$IMAGE" sh -c 'id -u; cat /coffre/dossier/note'
```

```text
bonjour
0
cat: can't open '/coffre/dossier/note': Permission denied
```

The uid is 0 and the access is refused: `DAC_OVERRIDE` is root's power to
ignore file rights. A container hardened with `--cap-drop` therefore behaves
like an ordinary user facing other people's files.

## 🧊 Exercise 5: an immutable file

Set the immutable attribute on a file of the host, then try to change it as
root in a container:

```bash
echo fige > fige.txt
sudo chattr +i fige.txt
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c 'stat -c %a /d/fige.txt; echo x >> /d/fige.txt'
lsattr fige.txt | cut -c1-6
sudo chattr -i fige.txt
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c 'echo x >> /d/fige.txt && tail -1 /d/fige.txt'
```

```text
664
sh: can't create /d/fige.txt: Operation not permitted
----i-
x
```

`Operation not permitted`, not `Permission denied`: the kernel does not discuss
rights, it forbids the operation. Neither `stat` nor the container's inspection
shows it. `lsattr`, on the host, shows the `i`.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-racine essai-noexec > /dev/null
rm -r ~/essai-refus
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset troubleshoot-permission-refusee
dsoxlab check troubleshoot-permission-refusee
```

```text
╭─ Result: troubleshoot-permission-refusee ─╮
│  0 / 100 pts                              │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests          │
╰───────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three refusals, three causes to tell apart,
and no repair as root.

```bash
dsoxlab run troubleshoot-permission-refusee
dsoxlab challenge troubleshoot-permission-refusee
```
