# Two containers, one volume, rights that hold

The lesson aligns a shared group, shows setgid and the creation mask. This
course adds five moves: a number that changes name, a missing account, a
missing group, removing someone else's file, and the owner of a copied file.

You work in `~/essai-droits`, on the `essai-commun` volume and `essai-*`
containers. The challenge uses `rapport`, `verificateur` and
`rapports-partages`: do not touch them during the course.

Related page: [Docker volume permissions: three common causes of an access denied](https://www.stephane-robert.info/en/docs/docker/volume-permissions/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run donnees-permissions-uid-gid
```

You are connected to `docker.lab`, where the engine runs, and the Alpine image
is on the machine. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🏷️ Exercise 1: one number, two names

Create a file in a container under an account that has the same number as
yours:

```bash
id -un
docker run --rm -v "$PWD:/d" "$IMAGE" sh -c "adduser -D -u $(id -u) paul; su paul -c 'touch /d/note'; ls -l /d/note | awk '{print \$3}'"
ls -l note | awk '{print $3}'
ls -ln note | awk '{print $3}'
```

```text
ansible
paul
ansible
1001
```

The container shows `paul`, the host shows your account, and it is the same
file. Only the number is recorded: each system translates it with its own
accounts file. To compare rights, read the numbers.

## 👤 Exercise 2: an account missing from the image

Ask for an account by its name, then by a number the image does not know:

```bash
docker run --rm --user paul "$IMAGE" id 2>&1 | grep -o 'unable to find user.*'
docker run --rm --user 4343 "$IMAGE" id
```

```text
unable to find user paul: no matching entries in passwd file
uid=4343 gid=0(root) groups=0(root)
```

A name is looked up in the image: if missing, it prevents the container from
starting. A number is always accepted. An account asked for by name therefore
reports an error that the number would let through.

## 👥 Exercise 3: a group missing from the image

Same test with an additional group:

```bash
docker run --rm --user 4343 --group-add equipage "$IMAGE" id 2>&1 | grep -io 'unable to find group.*'
docker run --rm --user 4343 --group-add 5151 "$IMAGE" id
```

```text
unable to find group equipage: no matching entries in group file
uid=4343 gid=0(root) groups=0(root),5151
```

`--group-add` follows the same rule. Number 5151 appears in `groups`, next to
the main group, still 0 (root): `--user 4343` only set the user.

## 🗑️ Exercise 4: removing someone else's file

Two accounts write to a directory open to everyone, such as `/tmp`. The second
removes the first one's file, then tries again with the sticky bit (`t`):

```bash
commun() { docker run --rm --user "$1" -v essai-commun:/c "$IMAGE" sh -c "$2"; }
commun 0:0 'chmod 777 /c'
commun 4343:5151 'echo a > /c/premier'
commun 4444:5151 'rm -f /c/premier && echo supprime'
commun 0:0 'chmod 1777 /c; stat -c %A /c'
commun 4343:5151 'echo a > /c/premier'
commun 4444:5151 'rm -f /c/premier'; echo "code: $?"
```

```text
supprime
drwxrwxrwt
rm: can't remove '/c/premier': Operation not permitted
code: 1
```

Removing a file requires the right to write in the directory, not in the file.
The sticky bit restricts removal to the owner of the file and the owner of the
directory. This is the setting of `/tmp`.

## 📥 Exercise 5: the owner of a copied file

Copy a file from the host into a non-root container, without then with the `-a`
option:

```bash
echo reglage > conf.txt
docker run -d --name essai-cible --user 4343 "$IMAGE" sleep 600 > /dev/null
docker cp -q conf.txt essai-cible:/tmp/sans
docker cp -q -a conf.txt essai-cible:/tmp/avec
docker exec essai-cible stat -c '%u:%g %n' /tmp/sans /tmp/avec
docker exec essai-cible sh -c 'echo x >> /tmp/sans'
```

```text
1001:1001 /tmp/sans
4343:0 /tmp/avec
sh: can't create /tmp/sans: Permission denied
```

Without the option, the file keeps the host's numbers: the application can read
it, not change it. With `-a`, it is given to the container's user, 4343, and to
its main group, 0. Always check the owner after a copy.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-cible > /dev/null
docker volume rm essai-commun
rm -r ~/essai-droits
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
essai-commun
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset donnees-permissions-uid-gid
dsoxlab check donnees-permissions-uid-gid
```

```text
╭─ Result: donnees-permissions-uid-gid ─╮
│  0 / 100 pts                          │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests      │
╰───────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: two different identities write to a volume
that is not open to everyone.

```bash
dsoxlab run donnees-permissions-uid-gid
dsoxlab challenge donnees-permissions-uid-gid
```
