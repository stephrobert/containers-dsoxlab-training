# Two variants from one base, and no dev mount left in deployment

The lesson assembles a base and its variants, and reads the effective
configuration. This course adds five situations: a relative path that changes
meaning, a comparison between variants, a naming mistake, a service lost while
deriving, and a profiled service that survives the shutdown.

You work in `~/essai-formes`, on an `essai-formes` project. The challenge uses
`/opt/lab-variantes`: do not touch it during the course.

Related page: [Development and deployment: explicit variants](https://www.stephane-robert.info/en/docs/docker/development-and-deployment-variants/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-profils-et-variantes
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write a base, and a
variant stored in a subdirectory. **Keep the same terminal until the cleanup**:
the variables only exist in it.

```bash
mkdir -p ~/essai-formes && cd ~/essai-formes
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
mkdir -p variantes donnees
cat > compose.yaml <<'EOF'
services:
  service:
    image: ${IMAGE}
    init: true
    command: sleep 600
  aide:
    image: ${IMAGE}
    init: true
    command: sleep 600
    profiles: ["aide"]
EOF
cat > variantes/atelier.yaml <<'EOF'
services:
  service:
    volumes:
      - ./donnees:/donnees
EOF
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🧭 Exercise 1: a relative path that changes meaning

Assemble both files in both orders and read the mount's source:

```bash
docker compose -f compose.yaml -f variantes/atelier.yaml config | grep 'source:' | sed "s|$HOME|~|"
docker compose -p essai-formes -f variantes/atelier.yaml -f compose.yaml config | grep 'source:' | sed "s|$HOME|~|"
```

```text
        source: ~/essai-formes/donnees
        source: ~/essai-formes/variantes/donnees
```

The relative paths of all the files start from the directory of the first `-f`.
In the second order, the mount points to a directory that does not exist, and
Compose says nothing.

## 🔍 Exercise 2: comparing two variants

Compare the effective configurations, not the files:

```bash
docker compose -f compose.yaml config > base.txt
docker compose -f compose.yaml -f variantes/atelier.yaml config > atelier.txt
diff base.txt atelier.txt | sed "s|$HOME|~|"
```

```text
10a11,15
>     volumes:
>       - type: bind
>         source: ~/essai-formes/donnees
>         target: /donnees
>         bind: {}
```

The difference between the two variants is five lines. This comparison,
replayed before each delivery, shows everything a variant adds, including what
nobody was looking for.

## ✏️ Exercise 3: a mistake in the service's name

Write a variant with the wrong name, without then with an image:

```bash
printf 'services:\n  servise:\n    restart: always\n' > faute.yaml
docker compose -f compose.yaml -f faute.yaml config -q
printf '    image: alpine\n' >> faute.yaml
docker compose -f compose.yaml -f faute.yaml config -q; echo "code: $?"
docker compose -f compose.yaml -f faute.yaml config --services | sort
```

```text
service "servise" has neither an image nor a build context specified: invalid compose project
code: 0
service
servise
```

An unknown name adds a service. Without an image, Compose refuses it; with an
image, it accepts it, and `service` did not receive `restart`. Read the list of
services again after each merge.

## 🧬 Exercise 4: a service lost while deriving

Derive the base with `extends`, then with `include`, and ask for the profile's
services:

```bash
cat > par-extends.yaml <<'EOF'
services:
  service:
    extends:
      file: compose.yaml
      service: service
EOF
printf 'include:\n  - compose.yaml\n' > par-include.yaml
docker compose -f par-extends.yaml --profile aide config --services | sort
echo '--'
docker compose -f par-include.yaml --profile aide config --services | sort
echo '--'
docker compose -f compose.yaml -f variantes/atelier.yaml --profile aide config --services | sort
```

```text
service
--
aide
service
--
aide
service
```

`extends` takes one named service, and only that one: `aide` is gone. `include`
and the list of `-f` take the whole file. Choose the method according to what
must follow.

## 👻 Exercise 5: a profiled service that survives the shutdown

Start with the profile, then shut down without it, in two ways:

```bash
docker compose --profile aide up -d
docker compose down
docker ps --format '{{.Names}}' | grep essai
docker compose -p essai-formes down
docker ps --format '{{.Names}}' | grep -c essai
```

```text
essai-formes-aide-1
0
```

The first `down` reads the file, where `aide` is off, and leaves it running.
With `-p`, Compose finds the containers by their project label and removes
`aide` too. Giving `--profile aide` again at shutdown also works.

## 🧹 Cleanup

```bash
cd ~
rm -r ~/essai-formes
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
dsoxlab reset compose-profils-et-variantes
dsoxlab check compose-profils-et-variantes
```

```text
╭─ Result: compose-profils-et-variantes ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests       │
╰────────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a base you cannot touch, two variants to
derive from it, and the right one to leave in service.

```bash
dsoxlab run compose-profils-et-variantes
dsoxlab challenge compose-profils-et-variantes
```
