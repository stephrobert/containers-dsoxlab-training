# Roll back a release, and refuse the one that would lose data

The lesson updates by digest and shows that a migration cannot be undone. This
course looks at what prevents a planned rollback: a tag that moved, an image
that can no longer be found, an image missing from the machine, a configuration
left ahead, and a lost refusal code.

You work in `~/essai-retour`, on an `essai-retour` project and `essai-appli`
images. The challenge uses the `dsoxlab-retour` project: do not touch it during
the course.

Related page: [Update, and roll back without losing data](https://www.stephane-robert.info/en/docs/docker/update-and-roll-back-without-losing-data/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-retour-arriere
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. The `fabrique`
function builds a version under a tag, `version` reads the running one. **Keep
the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-retour && cd ~/essai-retour
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
fabrique() { printf 'FROM %s\nRUN echo %s > /version\nCMD ["sleep","600"]\n' "$IMAGE" "$1" > Dockerfile; docker build -q -t "essai-appli:$2" .; }
version() { docker compose exec appli cat /version; }
cat > compose.yaml <<'EOF'
services:
  appli:
    image: ${APPLI:-essai-appli:stable}
    init: true
    pull_policy: ${POLITIQUE:-missing}
    environment:
      MODE: ${MODE:-prudent}
EOF
ID1=$(fabrique 1 stable)
docker compose up -d
version
```

```text
5.6.1
1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🏷️ Exercise 1: a tag that moved

Build version 2 under the same tag, restart, then apply again:

```bash
fabrique 2 stable > /dev/null
docker compose restart appli
version
docker compose up -d
version
docker inspect essai-retour-appli-1 --format '{{.Config.Image}}'
```

```text
1
2
essai-appli:stable
```

`restart` keeps the original image, `up -d` takes the one the tag now
designates. The file has not changed by one character, and the inspection shows
the same name: nothing in it says the version changed.

## 🕳️ Exercise 2: an image that can no longer be found

Try to go back to version 1 with the identifier noted at the start:

```bash
docker image inspect "$ID1" > /dev/null 2>&1; echo "code: $?"
APPLI="essai-appli@$ID1" docker compose up -d 2>&1 | grep -o 'pull access denied for essai-appli'
version
```

```text
code: 1
pull access denied for essai-appli
2
```

With the tag moved, nothing held version 1 any more once its container was
replaced. Compose then looks for it in a registry, where it was never
published. The service itself goes on with version 2: the failure broke
nothing, but there is no way back.

## 📌 Exercise 3: one tag per version

Build two versions under two tags, then go and come back:

```bash
fabrique 3 3.0 > /dev/null
fabrique 4 4.0 > /dev/null
APPLI=essai-appli:4.0 docker compose up -d; version
APPLI=essai-appli:3.0 docker compose up -d; version
docker compose config --images
APPLI=essai-appli:3.0 docker compose config --images
```

```text
4
3
essai-appli:stable
essai-appli:3.0
```

Each version keeps its name, hence its image: the rollback works. `config
--images` shows what Compose would deploy. Without the variable, it is still
`stable`: write the version in a file, otherwise the next `up -d` will forget
it.

## 📦 Exercise 4: an image missing from the machine

Put version 3 aside in a file, remove it, then come back to it:

```bash
docker save essai-appli:3.0 -o appli-3.tar
APPLI=essai-appli:4.0 docker compose up -d
docker rmi essai-appli:3.0 > /dev/null
APPLI=essai-appli:3.0 POLITIQUE=never docker compose up -d
version
docker load -q -i appli-3.tar
APPLI=essai-appli:3.0 POLITIQUE=never docker compose up -d
version
```

```text
Error response from daemon: No such image: essai-appli:3.0
4
Loaded image: essai-appli:3.0
3
```

`pull_policy: never` refuses at once, without querying a registry. The rollback
becomes possible again when the image is reloaded. Before an update, check that
the old image is on the machine or in a reachable registry.

## 🧾 Exercise 5: a configuration and an exit code

Go back to the old image without going back to the old setting, then read the
code of a program that refuses:

```bash
MODE=rapide APPLI=essai-appli:4.0 docker compose up -d
export MODE=rapide
APPLI=essai-appli:3.0 docker compose up -d
docker compose exec appli printenv MODE
unset MODE
docker run --rm essai-appli:3.0 sh -c 'echo refus >&2; exit 9' 2>&1 | cat; echo "tube: $?"
docker run --rm essai-appli:3.0 sh -c 'exit 9'; echo "direct: $?"
docker run --name essai-garde essai-appli:3.0 sh -c 'exit 9'
docker inspect essai-garde --format '{{.State.ExitCode}}'
```

```text
rapide
refus
tube: 0
direct: 9
9
```

The image came back, `MODE` stayed on the new value: a rollback concerns the
image and its configuration. As for the code, the pipe returns 0, the one of
`cat`. Run alone, `docker run` returns the program's code, and the inspection
of a kept container preserves it.

## 🧹 Cleanup

```bash
cd ~
docker compose -f ~/essai-retour/compose.yaml down
docker rm essai-garde > /dev/null
docker images --format '{{.Repository}}:{{.Tag}}' | grep '^essai-appli' | xargs docker rmi > /dev/null
rm -r ~/essai-retour
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
0
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset compose-retour-arriere
dsoxlab check compose-retour-arriere
```

```text
╭─ Result: compose-retour-arriere ──╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three versions, data to keep, and a rollback
that will no longer be possible.

```bash
dsoxlab run compose-retour-arriere
dsoxlab challenge compose-retour-arriere
```
