# Prevent privilege gain at runtime

The lesson sets the flag and checks that it is inherited. This course tests it
against a real setuid program, then shows how to list these programs, the ways
to write the option, the entries through `docker exec`, and a setuid program
that arrives through a volume.

You work in `~/essai-gain`, on the `essai-gain` image. It contains `lit`, a
setuid copy of a tool that displays a file. The challenge uses the `worker` of
its project: do not touch it during the course.

Related page: [Harden the runtime: capabilities and privileges](https://www.stephane-robert.info/en/docs/devsecops/containers-iac/docker-security/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run securite-no-new-privileges
```

You are connected to `docker.lab`, where the engine runs. `J` starts a
container under UID 1000. **Keep the same terminal until the cleanup**: the
variables only exist in it.

```bash
mkdir -p ~/essai-gain && cd ~/essai-gain
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
cat > Dockerfile <<'EOF'
ARG IMAGE
FROM $IMAGE
RUN cp /usr/bin/iconv /usr/local/bin/lit && chmod 4755 /usr/local/bin/lit
RUN cp /usr/bin/iconv /usr/local/bin/lit-g && chgrp shadow /usr/local/bin/lit-g && chmod 2755 /usr/local/bin/lit-g
EOF
docker build -q --build-arg IMAGE="$IMAGE" -t essai-gain . > /dev/null
J="docker run --rm --network none --user 1000:1000"
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔓 Exercise 1: a real privilege gain

Read a restricted file, with `cat`, then with the two copies:

```bash
$J essai-gain ls -l /etc/shadow | cut -c1-34
$J essai-gain head -c 5 /etc/shadow
$J essai-gain sh -c 'lit /etc/shadow | head -1'
$J essai-gain sh -c 'lit-g /etc/shadow | head -1'
$J --security-opt no-new-privileges essai-gain lit /etc/shadow
$J --security-opt no-new-privileges essai-gain lit-g /etc/shadow
```

```text
-rw-r-----    1 root     shadow
head: /etc/shadow: Permission denied
root:*::0:::::
root:*::0:::::
iconv: /etc/shadow: Permission denied
iconv: /etc/shadow: Permission denied
```

The container starts under UID 1000 and yet reads the file. The setuid bit
lends the owner's account, the setgid bit lends its group: both count. The flag
closes both.

## 🔍 Exercise 2: the inventory of an image

Look for an image's setuid and setgid programs, and look at what dropping
capabilities gives:

```bash
docker run --rm essai-gain find / -xdev -perm /6000 -type f | sort
docker run --rm "$IMAGE" find / -xdev -perm /6000 -type f | wc -l
$J --cap-drop ALL essai-gain sh -c 'lit /etc/shadow | head -1'
$J --cap-drop ALL essai-gain grep CapBnd /proc/1/status
```

```text
/usr/local/bin/lit
/usr/local/bin/lit-g
0
root:*::0:::::
CapBnd:	0000000000000000
```

Dropping all capabilities was not enough: `lit` becomes a root without special
power, but root owns the file. The two settings complement each other. And a
setuid program that is not in the image needs no blocking: make this inventory
at build time.

## ✍️ Exercise 3: the ways to write the option

Try six ways to write it and read the flag each time:

```bash
for o in no-new-privileges no-new-privileges:true no-new-privileges=true no-new-privileges:false no-new-privilege no-new-privileges:oui; do
  echo "$o -> $($J --security-opt "$o" essai-gain grep NoNewPrivs /proc/1/status 2>&1 | grep -oE 'NoNewPrivs.*|invalid --security-opt' | tr '\t' ' ')"
done
docker create --name essai-ecrit --security-opt no-new-privileges:false essai-gain true > /dev/null
docker inspect essai-ecrit --format '{{json .HostConfig.SecurityOpt}}'
docker rm essai-ecrit > /dev/null
```

```text
no-new-privileges -> NoNewPrivs: 1
no-new-privileges:true -> NoNewPrivs: 1
no-new-privileges=true -> NoNewPrivs: 1
no-new-privileges:false -> NoNewPrivs: 0
no-new-privilege -> invalid --security-opt
no-new-privileges:oui -> invalid --security-opt
["no-new-privileges:false"]
```

A typo is refused, but `:false` is accepted and protects nothing. In a review,
searching for the word `no-new-privileges` is therefore not enough. The proof
is `NoNewPrivs` in `/proc/1/status`.

## 🚪 Exercise 4: the entries through docker exec

Enter a protected container in three ways:

```bash
docker run -d --init --name essai-entree --user 1000:1000 --security-opt no-new-privileges essai-gain sleep 600 > /dev/null
docker exec essai-entree lit /etc/shadow
docker exec --privileged essai-entree lit /etc/shadow
docker exec --user 0 essai-entree head -c 5 /etc/shadow; echo
docker rm -f essai-entree > /dev/null
docker run --rm --security-opt no-new-privileges "$IMAGE" su nobody -s /bin/sh -c 'id -u'
```

```text
iconv: /etc/shadow: Permission denied
iconv: /etc/shadow: Permission denied
root:
65534
```

The flag applies to all added processes, even with `--privileged`. It does not
prevent entering directly as root with `--user 0`: that is not a gain, it is an
identity given at the start. And losing rights, like this root becoming
`nobody`, remains allowed.

## 📦 Exercise 5: a setuid program arriving through a volume

Put the setuid copy in a volume, then mount it in a container whose image has
none:

```bash
docker volume create essai-depot > /dev/null
docker run --rm -v essai-depot:/depot essai-gain sh -c 'cp /usr/local/bin/lit /depot/ && chmod 4755 /depot/lit'
$J -v essai-depot:/depot "$IMAGE" sh -c '/depot/lit /etc/shadow | head -1'
$J -v essai-depot:/depot --security-opt no-new-privileges "$IMAGE" /depot/lit /etc/shadow
docker run --rm --tmpfs /espace "$IMAGE" mount | grep -oE '/espace type tmpfs \(rw,nosuid'
docker volume rm essai-depot
```

```text
root:*::0:::::
iconv: /etc/shadow: Permission denied
/espace type tmpfs (rw,nosuid
essai-depot
```

The image inventory would have seen nothing: the program came with the data. A
tmpfs is mounted `nosuid`, a volume is not. This is why the flag stays useful
on a clean image.

## 🧹 Cleanup

```bash
cd ~
docker rmi -f essai-gain > /dev/null
rm -rf ~/essai-gain
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset securite-no-new-privileges
dsoxlab check securite-no-new-privileges
```

```text
╭─ Result: securite-no-new-privileges ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests     │
╰──────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a setuid program to keep, and a gain to make
impossible.

```bash
dsoxlab run securite-no-new-privileges
dsoxlab challenge securite-no-new-privileges
```
