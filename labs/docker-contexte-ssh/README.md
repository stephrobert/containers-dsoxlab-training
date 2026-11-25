# Create an SSH Docker context

The lesson creates an SSH context and proves that it reaches the other engine.
This course shows how one ends up on the wrong engine: a context left active, a
variable that comes first, a context that cannot be removed, an address
accepted without being checked, and a context that travels.

You work in `~/essai-contextes`, with a separate Docker configuration
directory: your real contexts are not touched. The challenge uses the
`docker-client.lab` VM: do not reach it during the course.

Related page: [Administer the Docker daemon and its contexts](https://www.stephane-robert.info/en/docs/docker/administer-the-docker-daemon-and-its-contexts/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-contexte-ssh
```

You are connected to `docker.lab`, where the engine runs. `DOCKER_CONFIG`
designates the separate directory. Two contexts: one leads to the local engine,
the other to a port where nothing listens. **Keep the same terminal until the
cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-contextes && cd ~/essai-contextes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
mkdir reglages && export DOCKER_CONFIG="$PWD/reglages"
docker context create essai-local --docker host=unix:///run/docker.sock > /dev/null 2>&1
docker context create essai-mort --docker host=tcp://127.0.0.1:1 > /dev/null 2>&1
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📌 Exercise 1: a context left active

Make a context active, then target another one for a single command:

```bash
docker context use essai-mort > /dev/null 2>&1
docker ps 2>&1 | grep -o 'Cannot connect.*1\.'
docker --context essai-local version --format '{{.Server.Version}}'
DOCKER_CONTEXT=essai-local docker context show
docker context show
```

```text
Cannot connect to the Docker daemon at tcp://127.0.0.1:1.
29.9.2
essai-local
essai-mort
```

`context use` holds for all terminals and all later sessions. `--context` holds
for one command, `DOCKER_CONTEXT` for one terminal. Before a command that
removes something, display `docker context show`.

## 🎭 Exercise 2: a variable that comes first

Set `DOCKER_HOST` while the broken context is active:

```bash
DOCKER_HOST=unix:///run/docker.sock docker version --format '{{.Server.Version}}'
DOCKER_HOST=unix:///run/docker.sock docker context show
DOCKER_HOST=unix:///run/docker.sock docker context use essai-local 2>&1 | grep -o 'DOCKER_HOST environment variable overrides the active context'
```

```text
29.9.2
default
DOCKER_HOST environment variable overrides the active context
```

`DOCKER_HOST` wins over the active context, silently: the command works
although the context is broken, and `context show` displays `default`. It is
the first variable to look at when a command does not target the expected
engine.

## 🧷 Exercise 3: a context that cannot be removed

Remove the active context, then the default context:

```bash
docker context rm essai-local 2>&1 | grep -o 'is in use'
docker context rm default 2>&1 | grep -o 'cannot be removed'
docker context use default > /dev/null 2>&1
docker context rm essai-local
docker context ls --format '{{.Name}} {{.Current}}'
```

```text
is in use
cannot be removed
essai-local
default true
essai-mort false
```

Docker refuses to remove the active context. Removing a context stops nothing
on the remote machine and revokes no key: it only erases an address on your
side.

## ✍️ Exercise 4: an address accepted without being checked

Create a context to an unknown host, then another one with an absurd protocol:

```bash
docker context create essai-loin --docker host=ssh://essai-inconnu 2> /dev/null
docker --context essai-loin ps 2>&1 | grep -oE 'exit status [0-9]+' | head -1
ssh -o ConnectTimeout=3 -o BatchMode=yes essai-inconnu true 2>&1 | grep -o 'Could not resolve hostname'
docker context create essai-absurde --docker host=ftp://a 2> /dev/null
docker context create essai-loin 2>&1 | grep -o 'already exists'
```

```text
essai-loin
exit status 255
Could not resolve hostname
essai-absurde
already exists
```

Creation succeeds in both cases: it does not try to connect. The error comes
later, and Docker's message hides `ssh`'s. Always try `ssh` alone first, with
the same name: it says why.

## 🧳 Exercise 5: a context that travels

Export a context, look at what the file contains, then import it back:

```bash
docker context export essai-loin loin.ctx
tar tf loin.ctx
tar xOf loin.ctx meta.json | grep -o '"Host":"[^"]*"'
docker context import essai-copie loin.ctx 2> /dev/null
docker context inspect essai-copie --format '{{.Endpoints.docker.Host}}'
```

```text
Written file "loin.ctx"
meta.json
tls
"Host":"ssh://essai-inconnu"
essai-copie
ssh://essai-inconnu
```

For an SSH context, the file only carries an address: no key, no password, no
setting from `~/.ssh/config`. At a colleague's, the alias must therefore exist
too. For a TLS context, on the other hand, the export contains the keys:
protect it like them.

## 🧹 Cleanup

```bash
cd ~
unset DOCKER_CONFIG
rm -rf ~/essai-contextes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-contexte-ssh
dsoxlab check docker-contexte-ssh
```

```text
╭─── Result: docker-contexte-ssh ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/2 tests  │
╰───────────────────────────────────╯
```

0 out of 2: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a second engine to reach, and a first one
that must remain the default.

```bash
dsoxlab run docker-contexte-ssh
dsoxlab challenge docker-contexte-ssh
```
