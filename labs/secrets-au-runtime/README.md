# Keep a runtime token out of Env

The lesson replaces a variable with a mounted file. This course follows the
secret after its delivery: what inherits a variable, what leaves a mounted
file, a rotation that does not show, a wrong fingerprint, a broadcast command,
and a Compose secret written in the container.

You work in `~/essai-jeton`, with an invented value, `essai-valeur`. The
challenge uses the `worker` of its project and its token: do not touch them
during the course.

Related page: [Keep a secret out of the environment](https://www.stephane-robert.info/en/docs/docker/keep-a-secret-out-of-the-environment/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run secrets-au-runtime
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-jeton && cd ~/essai-jeton
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
printf 'essai-valeur' > jeton && chmod 600 jeton
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🌿 Exercise 1: what inherits a variable

Pass the value with `-e`, then find it again in three places:

```bash
docker run -d --init --name essai-env -e JETON=essai-valeur "$IMAGE" sleep 600 > /dev/null
docker exec essai-env sh -c 'sh -c "env | grep JETON"'
sudo cat "/proc/$(docker inspect essai-env --format '{{.State.Pid}}')/environ" | tr '\0' '\n' | grep JETON
docker commit essai-env essai-image > /dev/null
docker inspect essai-image --format '{{json .Config.Env}}' | grep -o 'JETON=[a-z-]*'
docker rm -f essai-env > /dev/null; docker rmi -f essai-image > /dev/null
```

```text
JETON=essai-valeur
JETON=essai-valeur
JETON=essai-valeur
```

Each child process receives the variable, the host reads it, and `docker
commit` writes it into the image. An image published afterwards takes the
secret along.

## 📤 Exercise 2: what leaves a mounted file

Mount the file, then try to retrieve it by four means:

```bash
docker run -d --init --name essai-fichier -v "$PWD/jeton:/run/secrets/jeton:ro" "$IMAGE" sleep 600 > /dev/null
docker exec --user 1000 essai-fichier cat /run/secrets/jeton
docker cp -q essai-fichier:/run/secrets/jeton copie && cat copie; echo
docker export essai-fichier | tar xO run/secrets/jeton | wc -c
docker commit essai-fichier essai-image > /dev/null
docker run --rm essai-image sh -c 'wc -c < /run/secrets/jeton'
docker rmi -f essai-image > /dev/null
```

```text
cat: can't open '/run/secrets/jeton': Permission denied
essai-valeur
0
0
```

The file keeps the host's permissions: an ordinary account does not read it.
The export and the image only contain an empty file, the mount point. `docker
cp` follows the mount: whoever drives the engine reads the secret.

## 🔄 Exercise 3: a rotation that does not show

Replace the file with a new one, then modify it in place:

```bash
lit() { docker exec essai-fichier cat /run/secrets/jeton; echo; }
printf 'valeur-2' > neuf && chmod 600 neuf && mv neuf jeton
lit
docker restart --timeout 1 essai-fichier > /dev/null && lit
printf 'valeur-3' > jeton && lit
docker rm -f essai-fichier > /dev/null
```

```text
essai-valeur
valeur-2
valeur-3
```

After `mv`, the container still reads the old value: the mount holds on to the
file, not to its name. A restart updates it. Writing in place shows at once,
but the application may read in the middle of the write.

## #️⃣ Exercise 4: a wrong fingerprint

Compare the fingerprint of the same value, written in two ways:

```bash
echo 'essai-valeur' | sha256sum | cut -c1-12
printf 'essai-valeur' | sha256sum | cut -c1-12
echo 'essai-valeur' | wc -c; printf 'essai-valeur' | wc -c
```

```text
622e72c5798f
e3e48e631510
13
12
```

`echo` adds a newline, which changes the fingerprint and makes many logins
fail. Write a secret with `printf`, and compare sizes before looking further.

## 📻 Exercise 5: a broadcast command

Pass the value to `docker exec` in two ways, and read the engine's events:

```bash
docker run -d --init --name essai-cmd "$IMAGE" sleep 600 > /dev/null
DEBUT=$(date +%s)
docker exec -e JETON=essai-valeur essai-cmd true
docker exec essai-cmd true --jeton essai-valeur
sleep 1
docker events --since "$DEBUT" --until "$(date +%s)" --filter container=essai-cmd --format '{{.Action}}' | grep exec_create
docker rm -f essai-cmd > /dev/null
```

```text
exec_create: true
exec_create: true --jeton essai-valeur
```

The arguments of a command go into the events, which any tool plugged into the
engine can read. The variable is not there, but it stays readable on the host.
Give a secret through the command's input, or through a file.

## 🧾 Exercise 6: a Compose secret written in the container

Declare a secret whose source is a variable, and look for where it is:

```bash
cat > compose.yaml <<EOF
services:
  a:
    image: $IMAGE
    command: sleep 600
    init: true
    network_mode: none
    secrets: [jeton]
secrets:
  jeton:
    environment: JETON
EOF
JETON=essai-valeur docker compose -p essai-secret up -d > /dev/null 2>&1
docker inspect essai-secret-a-1 | grep -c essai-valeur
docker inspect essai-secret-a-1 --format '{{json .Mounts}}'
docker diff essai-secret-a-1 | grep secrets
docker exec essai-secret-a-1 stat -c '%a %U' /run/secrets/jeton
docker export essai-secret-a-1 | tar xO run/secrets/jeton; echo
JETON=x docker compose -p essai-secret down --timeout 1 > /dev/null 2>&1
```

```text
0
[]
A /run/secrets
A /run/secrets/jeton
444 root
essai-valeur
```

The inspection does not show it, and no mount exists: Compose copied the value
into the container's layer, readable by all its accounts. The export takes it
along. A `file` source gives a mount; that is the one a real secret needs.

## 🧹 Cleanup

```bash
cd ~
rm -rf ~/essai-jeton
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset secrets-au-runtime
dsoxlab check secrets-au-runtime
```

```text
╭─── Result: secrets-au-runtime ────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a token to deliver, which nothing must leak.

```bash
dsoxlab run secrets-au-runtime
dsoxlab challenge secrets-au-runtime
```
