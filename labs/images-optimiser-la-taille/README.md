# What a layer keeps

The lesson weighs three versions of one image. This course looks for other
hidden megabytes: a right changed too late, a context that is too wide, a file
copied twice, the space shared between images, and one size hiding another.

You work in `~/essai-poids`, on `essai-poids` images. The challenge uses
`/opt/lab-taille`: do not touch it during the course.

Related page: [Inspect and shrink a Docker image without breaking it](https://www.stephane-robert.info/en/docs/docker/inspect-and-shrink-an-image/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-optimiser-la-taille
```

You are connected to `docker.lab`, where the engine runs. Create a 20 MB file.
The `couches` function weighs the last layers of an image. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-poids && cd ~/essai-poids
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
dd if=/dev/urandom of=gros bs=1M count=20 2> /dev/null
couches() { docker history --format '{{.Size}} {{.CreatedBy}}' "essai-poids:$1" | head -"$2" | cut -c1-48; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🔑 Exercise 1: a right changed too late

Change the owner after the copy, then during the copy:

```bash
printf 'FROM %s\nCOPY gros /gros\nRUN chown 4242 /gros\n' "$IMAGE" > apres.Dockerfile
printf 'FROM %s\nCOPY --chown=4242 gros /gros\n' "$IMAGE" > pendant.Dockerfile
for f in apres pendant; do docker build -q -f $f.Dockerfile -t essai-poids:$f . > /dev/null; done
couches apres 2
couches pendant 1
```

```text
21MB RUN /bin/sh -c chown 4242 /gros # buildkit
21MB COPY gros /gros # buildkit
21MB COPY --chown=4242 gros /gros # buildkit
```

`chown` did not change one byte of the file, and the image carries it twice: a
layer records the whole file as soon as its attributes change. `chmod` and `mv`
have the same effect.

## 🧺 Exercise 2: a context that is too wide

Leave a directory lying in the context, copy everything, then exclude it:

```bash
mkdir vieux-rapports && dd if=/dev/urandom of=vieux-rapports/2019 bs=1M count=15 2> /dev/null
printf 'FROM %s\nCOPY . /appli\n' "$IMAGE" > tout.Dockerfile
docker build -q -f tout.Dockerfile -t essai-poids:tout . > /dev/null
docker run --rm essai-poids:tout du -sm /appli | cut -f1
printf 'vieux-rapports\n*.Dockerfile\n' > .dockerignore
docker build -q -f tout.Dockerfile -t essai-poids:tout . > /dev/null
docker run --rm essai-poids:tout du -sm /appli | cut -f1
docker run --rm essai-poids:tout ls -A /appli
```

```text
36
21
.dockerignore
gros
```

`COPY .` takes what is in the directory on the day of the build.
`.dockerignore` excludes it before it is sent to the engine. Notice that it is
in the image itself: add its own name to it, or copy the files one by one.

## 👯 Exercise 3: a file present twice

Give two names to the same content, in three ways:

```bash
printf 'FROM %s\nCOPY gros /a\nCOPY gros /b\n' "$IMAGE" > copie.Dockerfile
printf 'FROM %s\nCOPY gros /a\nRUN ln /a /b\n' "$IMAGE" > dur.Dockerfile
printf 'FROM %s\nCOPY gros /a\nRUN ln -s /a /b\n' "$IMAGE" > symbolique.Dockerfile
for f in copie dur symbolique; do docker build -q -f $f.Dockerfile -t essai-poids:$f . > /dev/null; echo "-- $f"; couches $f 1; done
```

```text
-- copie
21MB COPY gros /b # buildkit
-- dur
21MB RUN /bin/sh -c ln /a /b # buildkit
-- symbolique
4.1kB RUN /bin/sh -c ln -s /a /b # buildkit
```

The hard link, free on an ordinary disk, costs the whole file here: it is
created in another layer than the original. Only the symbolic link weighs
almost nothing.

## 🤝 Exercise 4: the space shared between images

Compare the announced size and the own share of two images that have the same
first layer:

```bash
docker system df -v --format '{{json .Images}}' > images.json
python3 -c "
import json
for x in json.load(open('images.json')):
    if x['Repository'] == 'essai-poids' and x['Tag'] in ('pendant', 'symbolique'):
        print(x['Tag'], x['Size'], 'propre:', x['UniqueSize'])
" | sort
```

```text
pendant 54.9MB propre: 41.96MB
symbolique 54.9MB propre: 8.115kB
```

Both images have the same size, but one costs almost nothing of its own: its
layers serve others. Removing an image returns its own share, not its size.
Look for space where `UniqueSize` is large.

## 🗜️ Exercise 5: one size hiding another

Compare an image full of zeros with an image full of random bytes:

```bash
printf 'FROM %s\nRUN dd if=/dev/zero of=/zero bs=1M count=20 2> /dev/null\n' "$IMAGE" > zero.Dockerfile
docker build -q -f zero.Dockerfile -t essai-poids:zero . > /dev/null
for f in zero pendant; do docker image ls "essai-poids:$f"; done | awk '/essai/{print $1, "disque", $3, "transfert", $4}'
```

```text
essai-poids:zero disque 33.9MB transfert 3.88MB
essai-poids:pendant disque 54.9MB transfert 24.8MB
```

The transfer is done on compressed layers: zeros shrink to almost nothing
there, randomness does not. `DISK USAGE` says what the image takes here,
`CONTENT SIZE` what travels. State which one you compare.

## 🧹 Cleanup

```bash
cd ~
docker images 'essai-poids' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-poids
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
dsoxlab reset images-optimiser-la-taille
dsoxlab check images-optimiser-la-taille
```

```text
╭─ Result: images-optimiser-la-taille ─╮
│  0 / 100 pts                         │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests     │
╰──────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: an image that is right from the inside, and
far too heavy.

```bash
dsoxlab run images-optimiser-la-taille
dsoxlab challenge images-optimiser-la-taille
```
