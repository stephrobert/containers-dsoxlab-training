# What comes from the base cannot be removed

The lesson separates build from runtime and fills an empty image. This course
looks at the passage from one stage to the next: what is not passed on, what
becomes of rights and links, a copy from another image, two copy mistakes, and
a stage nobody builds.

You work in `~/essai-etapes`, on `essai-etapes` images. The challenge uses
`/opt/lab-multietapes`: do not touch it during the course.

Related page: [Separate build from runtime: the multi-stage build](https://www.stephane-robert.info/en/docs/docker/build-in-multiple-stages/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-build-multi-etapes
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-etapes && cd ~/essai-etapes
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🚪 Exercise 1: what is not passed on

A stage sets a variable, a directory, a user and an argument. The next one
reads them:

```bash
cat > Dockerfile <<EOF
ARG EDITION=7
FROM $IMAGE AS atelier
ARG EDITION
ENV REGLAGE=oui
WORKDIR /atelier
USER 4242
RUN echo "\$REGLAGE \$(pwd) \$(id -u) \$EDITION" > /tmp/trace
FROM $IMAGE
COPY --from=atelier /tmp/trace /trace
RUN echo "[\$REGLAGE] \$(pwd) \$(id -u) [\$EDITION]" >> /trace
EOF
docker build -q -t essai-etapes:1 . > /dev/null
docker run --rm essai-etapes:1 cat /trace
```

```text
oui /atelier 4242 7
[] / 0 []
```

Nothing passes, except the copied file. A setting needed at runtime must be
repeated in the last stage, and an `ARG` declared before the first `FROM` must
be declared again in each stage that reads it.

## 🔑 Exercise 2: rights and links

Copy a file, a link alone, then the whole directory:

```bash
cat > droits.Dockerfile <<EOF
FROM $IMAGE AS atelier
RUN mkdir /s && echo 'echo lance' > /s/vrai && chmod 750 /s/vrai && chown 4242 /s/vrai && ln -s vrai /s/lien && ln -s /s/vrai /s/absolu
FROM $IMAGE
COPY --from=atelier /s/vrai /d/vrai
COPY --from=atelier --chown=1000:1000 --chmod=755 /s/vrai /d/choisi
COPY --from=atelier /s/lien /d/seul
COPY --from=atelier /s /d/tout
EOF
docker build -q -f droits.Dockerfile -t essai-etapes:2 . > /dev/null
docker run --rm essai-etapes:2 sh -c 'stat -c "%u:%g %a %F %n" /d/vrai /d/choisi /d/seul /d/tout/lien'
docker run --rm essai-etapes:2 cat /d/tout/absolu
```

```text
4242:0 750 regular file /d/vrai
1000:1000 755 regular file /d/choisi
4242:0 750 regular file /d/seul
0:0 777 symbolic link /d/tout/lien
cat: can't open '/d/tout/absolu': No such file or directory
```

The owner and the mode follow the file, unless `--chown` and `--chmod` set
them. A link copied alone becomes the file it points to. Inside a directory, it
stays a link: if it targets an absolute path of the previous stage, it is
broken.

## 📦 Exercise 3: copying from another image

`--from` also accepts an image that is not a stage:

```bash
cat > autre.Dockerfile <<EOF
FROM $IMAGE
COPY --from=$IMAGE /etc/alpine-release /socle
EOF
docker build -q -f autre.Dockerfile -t essai-etapes:3 . > /dev/null
docker run --rm essai-etapes:3 cat /socle
```

```text
3.24.3
```

You take a file from an image without starting from it. Pin that image by its
digest like the one of `FROM`: it provides content in the same way.

## ✏️ Exercise 4: two copy mistakes

Get the stage name wrong, then the path:

```bash
cat > faute.Dockerfile <<EOF
FROM $IMAGE AS atelier
RUN echo produit > /p
FROM $IMAGE
COPY --from=atelie /p /p
EOF
docker build -q -f faute.Dockerfile . 2>&1 | grep -o 'docker.io/library/atelie:latest' | head -1
sed -i 's/--from=atelie /--from=atelier /; s|/p /p|/q /q|' faute.Dockerfile
docker build -q -f faute.Dockerfile . 2>&1 | grep -o '"/q": not found' | head -1
```

```text
docker.io/library/atelie:latest
"/q": not found
```

An unknown stage becomes an image name: Docker looks for it on Docker Hub, and
the error is about denied access. The worst case is when such an image exists.
The second error is more direct and names the path.

## 💤 Exercise 5: a stage nobody builds

A stage fails, but the last one does not depend on it. Build the image, then
the stage:

```bash
cat > dormant.Dockerfile <<EOF
FROM $IMAGE AS controle
RUN exit 7
FROM $IMAGE
RUN echo ok > /ok
EOF
docker build -q -f dormant.Dockerfile -t essai-etapes:5 . > /dev/null; echo "code: $?"
docker build -q -f dormant.Dockerfile --target controle . 2>&1 | grep -o 'exit code: 7' | head -1
docker build -q -f dormant.Dockerfile --target rien . 2>&1 | grep -o 'target stage.*' | head -1
```

```text
code: 0
exit code: 7
target stage "rien" could not be found
```

The build succeeds without having played the failing stage. A check placed in a
stage only protects if the rest depends on it, or if you build it with
`--target`.

## 🧹 Cleanup

```bash
cd ~
docker images 'essai-etapes' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-etapes
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
0
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset images-build-multi-etapes
dsoxlab check images-build-multi-etapes
```

```text
╭─ Result: images-build-multi-etapes ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests    │
╰─────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: a product to deliver, without the tooling
that made it.

```bash
dsoxlab run images-build-multi-etapes
dsoxlab challenge images-build-multi-etapes
```
