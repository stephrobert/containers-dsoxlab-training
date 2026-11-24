# Separate frontend and data networks with Compose

The lesson spreads the services over several networks and tests each path. This
course adds five situations: a name valid on one side only, a live connection
that does not last, two declaration mistakes, a network shared by two projects,
and a network `down` does not remove.

You work in `~/essai-cotes`, on the `essai-cotes` and `essai-voisin` projects.
The challenge uses the `dsoxlab-isolation-reseau` project: do not touch it
during the course.

Related page: [Organize the networks of a Compose stack](https://www.stephane-robert.info/en/docs/docker/organize-the-networks-of-a-stack/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run compose-isolation-reseau
```

You are connected to `docker.lab`. The `COMPOSE_PROGRESS` variable silences
Compose's progress: only warnings and errors are printed. Write three services,
then a function that says whether one reaches another. **Keep the same terminal
until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-cotes && cd ~/essai-cotes
export COMPOSE_PROGRESS=quiet
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker compose version --short
cat > compose.yaml <<'EOF'
x-base: &base
  image: ${IMAGE}
  init: true
  command: sleep 600
services:
  pont:
    <<: *base
    networks:
      rive-a:
        aliases:
          - passage
      rive-b:
  gauche:
    <<: *base
    networks:
      - rive-a
  droite:
    <<: *base
    networks:
      - rive-b
networks:
  rive-a:
  rive-b:
EOF
joint() { docker compose exec "$1" ping -c1 -W2 "$2" > /dev/null 2>&1 && echo "$1 joint $2" || echo "$1 ne joint pas $2"; }
docker compose up -d
```

```text
5.6.1
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 24
November 2026. Addresses and identifiers will differ on your side.

## 🏷️ Exercise 1: a name valid on one side only

The `pont` service has a second name, `passage`, on `rive-a` only:

```bash
joint gauche passage
joint droite passage
joint droite pont
```

```text
gauche joint passage
droite ne joint pas passage
droite joint pont
```

An alias belongs to the network where it is declared, not to the service.
`droite` knows `pont` under its service name, and does not know `passage`.

## 🔌 Exercise 2: a live connection

Connect `gauche` to `rive-b` by hand, then recreate it:

```bash
joint gauche droite
docker network connect essai-cotes_rive-b essai-cotes-gauche-1
joint gauche droite
docker compose up -d --force-recreate gauche
joint gauche droite
```

```text
gauche ne joint pas droite
gauche joint droite
gauche ne joint pas droite
```

The manual connection works at once, and disappears at recreation: only the
file is authoritative. An isolation, or a path, that the file does not describe
does not hold.

## 🚫 Exercise 3: two declaration mistakes

Have an undeclared network validated, then a service without network that asks
for one:

```bash
sed '/  gauche:/,/  droite:/s/- rive-a/- rive-z/' compose.yaml > faute.yaml
docker compose -f faute.yaml config -q 2>&1 | grep -o 'service.*'
sed '/  gauche:/a\    network_mode: none' compose.yaml > mode.yaml
docker compose -f mode.yaml config -q 2>&1 | grep -o 'service.*'
```

```text
service "gauche" refers to undefined network rive-z: invalid compose project
service gauche declares mutually exclusive `network_mode` and `networks`: invalid compose project
```

Compose refuses both before creating anything. A network name must appear in
the `networks:` block at the bottom, and `network_mode` is used instead of
`networks:`, never with it.

## 🤝 Exercise 4: a network shared by two projects

A second project connects to a network it does not create:

```bash
cat > voisin.yaml <<'EOF'
services:
  visiteur:
    image: ${IMAGE}
    init: true
    command: sleep 600
    networks:
      - commun
networks:
  commun:
    external: true
    name: ${RESEAU}
EOF
RESEAU=essai-absent docker compose -p essai-voisin -f voisin.yaml up -d 2>&1 | grep -o 'network essai-absent.*'
export RESEAU=essai-cotes_rive-b
docker compose -p essai-voisin -f voisin.yaml up -d
docker compose -p essai-voisin -f voisin.yaml exec visiteur ping -c1 -W2 droite | grep -o '1 packets received'
```

```text
network essai-absent declared as external, but could not be found
1 packets received
```

`external: true` tells Compose that the network already exists: it does not
create it and will not remove it. Missing, it is an error. Present, it lets
`visiteur` into `rive-b`, where it reaches `droite`. So also check who, outside
your file, is connected to your networks.

## 🧷 Exercise 5: a network `down` does not remove

Take the first project down while the second one still uses its network:

```bash
docker compose down
docker network ls --format '{{.Name}}' | grep essai-cotes
docker network inspect essai-cotes_rive-b --format '{{range .Containers}}{{.Name}} {{end}}'
docker compose -p essai-voisin -f voisin.yaml down
docker compose down
docker network ls --format '{{.Name}}' | grep -c essai-cotes
```

```text
essai-cotes_rive-b
essai-voisin-visiteur-1
0
```

Docker does not remove a network in use. `docker network inspect` gives the
occupant. Once it is gone, a second `down` removes the network.

## 🧹 Cleanup

```bash
cd ~
rm -r ~/essai-cotes
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
dsoxlab reset compose-isolation-reseau
dsoxlab check compose-isolation-reseau
```

```text
╭─ Result: compose-isolation-reseau ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests   │
╰────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: three services, two zones, and a path that
must stay closed.

```bash
dsoxlab run compose-isolation-reseau
dsoxlab challenge compose-isolation-reseau
```
