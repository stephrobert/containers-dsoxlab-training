# Keep application data across Compose recreation

The lesson follows the data of a database through recreations. This course adds
five situations: data that seems lost, a volume Compose does not manage, a
naming mistake, what an empty volume receives from the image, and a volume
removed from the file.

You work in `~/essai-garde`, on `essai-*` projects and volumes. The challenge
uses the `dsoxlab-persistance` project: do not touch it during the course.

Related page: [Persist the data of a recreated stack](https://www.stephane-robert.info/en/docs/docker/persist-the-data-of-a-recreated-stack/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-persistance
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a service and
its volume, then put a line in it. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-garde && cd ~/essai-garde
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  carnet:
    image: ${IMAGE}
    init: true
    command: sleep 600
    volumes:
      - pages:/pages
volumes:
  pages:
EOF
docker compose up -d
docker compose exec carnet sh -c 'echo ligne-1 > /pages/notes'
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🫥 Exercise 1: data that seems lost

Start the same file under another project name:

```bash
docker compose -p essai-bis up -d
docker compose -p essai-bis exec carnet ls -A /pages | wc -l
docker volume ls --format '{{.Name}}' | grep essai
docker volume inspect essai-garde_pages --format '{{index .Labels "com.docker.compose.project"}}'
docker compose -p essai-bis down -v
```

```text
0
essai-bis_pages
essai-garde_pages
essai-garde
```

The volume's name contains the project's: renaming the directory or changing
`-p` makes an empty volume. The data is still in the first volume. Its label
says which project it belongs to.

## 🔒 Exercise 2: a volume Compose does not manage

Declare an external volume, before then after creating it, and run a `down -v`:

```bash
sed 's/^  pages:$/  pages: {external: true, name: essai-coffre}/' compose.yaml > externe.yaml
docker compose -p essai-ext -f externe.yaml up -d 2>&1 | grep -o 'external volume.*'
docker volume create essai-coffre
docker compose -p essai-ext -f externe.yaml up -d
docker compose -p essai-ext -f externe.yaml down -v
docker volume ls --format '{{.Name}}' | grep coffre
```

```text
external volume "essai-coffre" not found
essai-coffre
essai-coffre
```

An external volume is created separately, and `down -v` does not erase it. It
is a protection against a hasty command, which in return asks you to create and
remove it yourself.

## ✏️ Exercise 3: a naming mistake

Make a mistake in the volume's name, then forget the dot of a relative path:

```bash
sed 's/- pages:/- page:/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed 's|- pages:|- ./pages:|' compose.yaml > chemin.yaml
docker compose -f chemin.yaml config | grep -A1 'volumes:' | grep type
```

```text
service "carnet" refers to undefined volume page: invalid compose project
      - type: bind
```

Compose refuses a name that is not declared at the bottom of the file. With
`./`, it no longer looks for a volume but for a directory of the host: the type
goes from `volume` to `bind`, and the data moves elsewhere without any error.
Check the type in `config`.

## 📦 Exercise 4: what an empty volume receives from the image

Mount two empty volumes on directories the image fills, one with `nocopy`:

```bash
cat > copie.yaml <<'EOF'
services:
  app:
    image: ${IMAGE}
    init: true
    command: sleep 600
    volumes:
      - avec:/etc/apk
      - type: volume
        source: sans
        target: /etc/ssl
        volume:
          nocopy: true
volumes:
  avec:
  sans:
EOF
docker compose -p essai-copie -f copie.yaml up -d
docker compose -p essai-copie -f copie.yaml exec app sh -c 'ls -A /etc/apk | wc -l; ls -A /etc/ssl | wc -l'
docker compose -p essai-copie -f copie.yaml down -v
```

```text
5
0
```

The first volume received the files of the image, the second stayed empty. The
copy happens only once, when the volume is empty: a newer image will not change
it.

## 🗂️ Exercise 5: a volume removed from the file

Remove the volume from the file, apply, then run `down -v`:

```bash
sed -i '/volumes:/d;/pages/d' compose.yaml
docker compose up -d
docker compose down -v
docker volume ls --format '{{.Name}}' | grep garde
docker run --rm -v essai-garde_pages:/p "$IMAGE" cat /p/notes
```

```text
essai-garde_pages
ligne-1
```

`down -v` only removes the volumes the file still declares. The volume removed
from the file stays on the machine with its data: you can read it again, and it
is also the one that fills the disk if nobody looks for it.

## 🧹 Cleanup

```bash
cd ~
docker volume rm essai-garde_pages essai-coffre
rm -r ~/essai-garde
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker network ls --format '{{.Name}}' | grep -c '^essai-'
docker volume ls --format '{{.Name}}' | grep -c '^essai-'
```

```text
essai-garde_pages
essai-coffre
0
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset compose-persistance
dsoxlab check compose-persistance
```

```text
╭─── Result: compose-persistance ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: writes that must survive the disappearance of
their container.

```bash
dsoxlab run compose-persistance
dsoxlab challenge compose-persistance
```
