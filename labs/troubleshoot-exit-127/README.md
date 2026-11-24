# Three failures, three exit codes to read

The lesson gives the grid of codes 125, 126 and 127, and says where to read the
error. This course makes you meet five failures whose first diagnosis is
misleading: a missing interpreter, a file written on Windows, quotes too many, a
right that depends on the user, and a container that never started.

You work in `~/essai-codes`, on `essai-*` containers. The challenge uses
`panne-a`, `panne-b` and `panne-c`: do not touch them during the course.

Related page: [Read a Docker startup failure: exit codes and loops](https://www.stephane-robert.info/en/docs/docker/read-a-startup-failure/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run troubleshoot-exit-127
```

You are connected to `docker.lab`, where the engine runs. The `lire` function
shows the status, the code and the error of a container. **Keep the same
terminal until the cleanup.**

```bash
mkdir -p ~/essai-codes && cd ~/essai-codes
IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
lire() { docker container inspect "$1" --format 'statut={{.State.Status}} code={{.State.ExitCode}} erreur={{.State.Error}}'; }
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on
24 November 2026.

## 🐚 Exercise 1: the file exists, and Docker says otherwise

This script exists and is executable. Its first line asks for `bash`, which the
Alpine image does not hold:

```bash
printf '#!/bin/bash\necho bonjour\n' > lancer.sh
chmod 755 lancer.sh
docker run --name essai-bash -v "$PWD:/outils:ro" "$IMAGE" /outils/lancer.sh > /dev/null 2>&1
lire essai-bash
docker logs essai-bash
docker run --rm "$IMAGE" ls /bin/bash
```

```text
statut=exited code=255 erreur=
exec /outils/lancer.sh: no such file or directory
ls: /bin/bash: No such file or directory
```

The message names `lancer.sh`, which does exist. The missing file is its
interpreter, `/bin/bash`. The code is 255, outside the grid, and `.State.Error`
is empty: the message is in the logs. The last command confirms that `bash` is
not in the image.

## 🪟 Exercise 2: Windows line endings

Same message, another cause: this script asks for `/bin/sh`, which does exist.

```bash
printf '#!/bin/sh\r\necho bonjour\r\n' > windows.sh
chmod 755 windows.sh
docker run --name essai-windows -v "$PWD:/outils:ro" "$IMAGE" /outils/windows.sh > /dev/null 2>&1
lire essai-windows
docker logs essai-windows
head -1 windows.sh | od -c
sed -i 's/\r$//' windows.sh
docker run --rm -v "$PWD:/outils:ro" "$IMAGE" /outils/windows.sh
```

```text
statut=exited code=255 erreur=
exec /outils/windows.sh: no such file or directory
0000000   #   !   /   b   i   n   /   s   h  \r  \n
0000013
bonjour
```

`od -c` shows `\r` before `\n`: the file comes from a Windows editor. The
kernel looked for a program named `/bin/sh` followed by this invisible character.
The `sed` removes it and the script runs. Facing this message, check the
interpreter, then the line endings.

## ✂️ Exercise 3: quotes too many

Compare the same kind of command with and without quotes around the whole:

```bash
docker run --name essai-guillemets "$IMAGE" "ls -l /etc/hostname" > /dev/null 2>&1
lire essai-guillemets | cut -c1-60
docker container inspect essai-guillemets --format '{{json .Config.Cmd}}'
docker run --name essai-separes "$IMAGE" ls /etc/alpine-release
docker container inspect essai-separes --format '{{json .Config.Cmd}}'
```

```text
statut=created code=127 erreur=failed to create task for con
["ls -l /etc/hostname"]
/etc/alpine-release
["ls","/etc/alpine-release"]
```

With the quotes, `.Config.Cmd` holds a single element: Docker looks for a program
whose name contains spaces, hence code 127. Without them, there are two elements,
the program and its argument. Read `.Config.Cmd` before suspecting the image.

## 🔑 Exercise 4: a right that depends on the user

This script can only be read by its owner. Run it as uid 4242, then as root:

```bash
printf '#!/bin/sh\necho bonjour\n' > prive.sh
chmod 700 prive.sh
docker run --name essai-prive --user 4242 -v "$PWD:/outils:ro" "$IMAGE" /outils/prive.sh > /dev/null 2>&1
lire essai-prive
docker logs essai-prive
docker run --rm -v "$PWD:/outils:ro" "$IMAGE" /outils/prive.sh
```

```text
statut=exited code=2 erreur=
/bin/sh: can't open '/outils/prive.sh': Permission denied
bonjour
```

The code is not 126 but 2, and the container did start: the shell returned this
code, as it could not read the script. As root, it runs. The same file can
therefore succeed or fail depending on `--user`.

## 📦 Exercise 5: search a container that never started

`docker exec` is useless on a container that did not start. Its files can still
be read:

```bash
docker create --name essai-jamais "$IMAGE" outil-absent > /dev/null
lire essai-jamais
docker export essai-jamais | tar -t | grep -E '^bin/(sh|bash)$|outil-absent'
docker cp essai-jamais:/etc/alpine-release - | tar -xO
```

```text
statut=created code=0 erreur=
bin/sh
3.24.3
```

`docker export` returns the whole file system as an archive, which `tar -t`
lists: `sh` is there, `bash` and `outil-absent` are not. You answer the question
"is this program in the image?" without running anything.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-bash essai-windows essai-guillemets essai-separes essai-prive essai-jamais > /dev/null
rm -r ~/essai-codes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset troubleshoot-exit-127
dsoxlab check troubleshoot-exit-127
```

```text
╭── Result: troubleshoot-exit-127 ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: read three failures, note their codes and the
status of one of them, then start a container that runs on the same image.

```bash
dsoxlab run troubleshoot-exit-127
dsoxlab challenge troubleshoot-exit-127
```
