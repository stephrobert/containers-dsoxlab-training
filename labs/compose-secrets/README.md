# Grant a Compose secret only to its consumer

The lesson grants a file secret to a service, then replaces it. This course
adds five situations: a secret taken from the machine's environment, a
different name in the container, one newline too many, two declaration
mistakes, and a copy that ends up in an image.

You work in `~/essai-cles`, on an `essai-cles` project, with demonstration
values. The challenge uses `/opt/lab-compose-secret`: do not touch it during
the course.

Related page: [Inject secrets, and know their limits](https://www.stephane-robert.info/en/docs/docker/inject-secrets-and-know-their-limits/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-secrets
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a service that
receives a secret. **Keep the same terminal until the cleanup**: the variables
only exist in it.

```bash
mkdir -p ~/essai-cles && cd ~/essai-cles
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
services:
  caisse:
    image: ${IMAGE}
    init: true
    command: sleep 600
    secrets:
      - source: cle
        target: cle_de_caisse
secrets:
  cle:
    file: ./cle.txt
EOF
printf 'valeur-demo\n' > cle.txt
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🏷️ Exercise 1: another name in the container

Start and look for the secret under its two names:

```bash
docker compose up -d
docker compose exec caisse ls /run/secrets
docker compose exec caisse cat /run/secrets/cle
```

```text
cle_de_caisse
cat: can't open '/run/secrets/cle': No such file or directory
```

The long form separates `source`, the name in the block at the bottom, and
`target`, the name of the file the application reads. Only the second one
exists in the container.

## ↩️ Exercise 2: one newline too many

Count the bytes the container receives, then compare two ways of reading the
value:

```bash
printf 'valeur-demo' | wc -c
docker compose exec caisse sh -c 'wc -c < /run/secrets/cle_de_caisse'
docker compose exec caisse sh -c 'printf valeur-demo | cmp - /run/secrets/cle_de_caisse'
docker compose exec caisse sh -c '[ "$(cat /run/secrets/cle_de_caisse)" = valeur-demo ] && echo egal'
```

```text
11
12
cmp: EOF on -
egal
```

The file holds one more byte: the newline. A shell removes it when reading, a
program that reads every byte keeps it, and authentication fails with a value
that looks right. Write the secret with `printf`, without `\n`, or check that
the application removes that character.

## 🚫 Exercise 3: two declaration mistakes

Grant a secret nobody declares, then declare a missing file:

```bash
sed 's/source: cle$/source: clef/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed 's/cle.txt/rien.txt/' compose.yaml > absent.yaml
docker compose -f absent.yaml config -q; echo "code: $?"
docker compose -p essai-absent -f absent.yaml up -d 2>&1 | grep -o 'bind source path does not exist'
docker compose -p essai-absent -f absent.yaml down
```

```text
service "caisse" refers to undefined secret clef: invalid compose project
code: 0
bind source path does not exist
```

`config` refuses an unknown name, but does not check that the file exists: it
returns 0. The error comes at startup, and the project's network has already
been created. Hence the `down`.

## 🌍 Exercise 4: a secret taken from the environment

Take the value from a variable of the machine, then look for it where it should
not be:

```bash
sed 's|file: ./cle.txt|environment: CLE_POSTE|' compose.yaml > env.yaml
docker compose -p essai-env -f env.yaml up -d 2>&1 | grep -o 'environment variable.*'
export CLE_POSTE=autre-demo
docker compose -p essai-env -f env.yaml up -d
docker inspect essai-env-caisse-1 | grep -c autre-demo
docker export essai-env-caisse-1 | grep -a -c autre-demo
docker export essai-cles-caisse-1 | grep -a -c valeur-demo
docker compose -p essai-env -f env.yaml down
unset CLE_POSTE
```

```text
environment variable "CLE_POSTE" required by secret "essai-env_cle" is not set
0
1
0
```

The value is missing from the inspection, but present in the export: with no
file to mount, Compose copied it into the container's write layer. With a file,
the export holds nothing. The source therefore changes where the value ends up
on disk.

## 📸 Exercise 5: a copy that ends up in an image

Do as a startup script that copies the secret, then freeze the container into
an image:

```bash
docker compose exec caisse sh -c 'cat /run/secrets/cle_de_caisse > /tmp/copie'
docker commit essai-cles-caisse-1 essai-cles:fuite > /dev/null
docker run --rm essai-cles:fuite cat /tmp/copie
docker run --rm essai-cles:fuite cat /run/secrets/cle_de_caisse
docker rmi -f essai-cles:fuite > /dev/null
```

```text
valeur-demo
```

The mount did not follow: the file is there but empty. The copy went into the
image, readable by everyone who receives it. A mounted secret does not protect
from an application that copies it.

## 🧹 Cleanup

```bash
cd ~
docker compose -f ~/essai-cles/compose.yaml down
rm -r ~/essai-cles
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
dsoxlab reset compose-secrets
dsoxlab check compose-secrets
```

```text
╭───── Result: compose-secrets ─────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: one token, a single service that reads it,
and a value to replace.

```bash
dsoxlab run compose-secrets
dsoxlab challenge compose-secrets
```
