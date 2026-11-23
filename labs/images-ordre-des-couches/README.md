# Order a Dockerfile for the cache

The lesson shows how the builder decides to reuse a layer, in which order to
write the instructions, and how a `.dockerignore` keeps the cache stable.
This course has you see three things it does not show: the position of an
`ARG` can make an installation run again, a `RUN` can stay frozen by the
cache and be refreshed from a chosen point, and `docker builder prune` does
not empty the cache your images still use.

You work in `~/essai-cache`, with `essai-cache:*` images. The challenge uses
another application and another Dockerfile: you will do it on your own, at
the end.

Related page: [Dockerfile best practices](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/) (in French).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-ordre-des-couches
```

You are now connected to `docker.lab`, a Debian 13 machine where the Docker
engine runs. Create the scratch directory, store the base image in a
variable, and define a small `etapes` function. It reads the output of a
build and prints each step, followed by `CACHED` when the builder reused it.
**Keep the same terminal until the clean-up**: the variable and the function
only exist in it.

```bash
mkdir -p ~/essai-cache && cd ~/essai-cache
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
etapes() { awk '/^#[0-9]+ \[[0-9]\/[0-9]\]/ { n=$1; sub(/^#[0-9]+ /, ""); if ($0 !~ /^\[1\//) { ligne[n]=$0; ordre[++k]=n } next } /^#[0-9]+ CACHED/ { cache[$1]=1 } END { for (i=1;i<=k;i++) print ligne[ordre[i]] (cache[ordre[i]] ? "  CACHED" : "") }'; }
```

The outputs in this course were captured on this machine on 23 November
2026, with Docker Engine 29.9.2.

## 🏷️ Exercise 1: the position of an `ARG`

An `ARG` is a value passed to the build with `--build-arg`. It is visible to
the `RUN` instructions that follow it, and changing it can make them run
again. Write a Dockerfile that declares `ETIQUETTE` at the top, before an
installation that does not use it. Build once, then build again with a new,
unique value taken from the clock:

```bash
cat > Dockerfile.haut <<EOF
FROM $ALPINE
ARG ETIQUETTE=a
RUN apk add --no-cache jq >/dev/null && jq --version
RUN echo "etiquette=\$ETIQUETTE" > /etiquette
EOF
docker build -q -t essai-cache:haut -f Dockerfile.haut . >/dev/null
docker build --progress=plain -t essai-cache:haut -f Dockerfile.haut --build-arg ETIQUETTE="$(date +%s)" . 2>&1 | etapes
```

```text
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version
[3/3] RUN echo "etiquette=1795458824" > /etiquette
```

The `jq` installation ran again, although it does not use `ETIQUETTE`:
declared above it, the value is part of its environment, and so of what the
builder compares. Move the `ARG` right before the step that uses it, and try
again:

```bash
cat > Dockerfile.bas <<EOF
FROM $ALPINE
RUN apk add --no-cache jq >/dev/null && jq --version
ARG ETIQUETTE=a
RUN echo "etiquette=\$ETIQUETTE" > /etiquette
EOF
docker build -q -t essai-cache:bas -f Dockerfile.bas . >/dev/null
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE="$(date +%s)" . 2>&1 | etapes
```

```text
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version  CACHED
[3/3] RUN echo "etiquette=1795458826" > /etiquette
```

This time, the installation is served by the cache, and only the last step
runs again. An `ARG` is therefore declared as close as possible to the step
that uses it, just as a file is copied as close as possible to the step that
reads it.

## 🕰️ Exercise 2: a frozen `RUN`, and refreshing it from a point

The lesson warns that a `RUN` whose text does not change is always served by
the cache. Make it visible with a command that records the time. The
Dockerfile records two times, separated by an `ARG RAFRAICHIR`:

```bash
cat > Dockerfile.date <<EOF
FROM $ALPINE
RUN date +%H:%M:%S > /construit-a
ARG RAFRAICHIR=0
RUN date +%H:%M:%S > /rafraichi-a
EOF
docker build -q -t essai-cache:date -f Dockerfile.date . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
sleep 3; docker build -q -t essai-cache:date -f Dockerfile.date . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
sleep 3; docker build -q -t essai-cache:date -f Dockerfile.date --build-arg RAFRAICHIR="$(date +%s)" . >/dev/null
docker run --rm essai-cache:date cat /construit-a /rafraichi-a
```

```text
18:31:41
18:33:47
18:31:41
18:33:47
18:31:41
18:33:55
```

The second build gives the same times as the first: nothing ran, both
layers come from the cache. On the third one, the value of `RAFRAICHIR`
changes: the second time is new, the first one is still that of the very
first build. Placed right before the steps to refresh (a package update, for
example), such an `ARG` makes them run again without rebuilding everything
else. `--no-cache`, on the other hand, rebuilds everything.

## 🧹 Exercise 3: what `docker builder prune` really empties

`docker builder prune` deletes the build cache. Run it, then rebuild
`essai-cache:bas` with a value already built:

```bash
docker build -q -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . >/dev/null
docker builder prune -f | tail -1
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . 2>&1 | etapes
```

```text
Total:	2.876MB
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version  CACHED
[3/3] RUN echo "etiquette=b" > /etiquette  CACHED
```

The clean-up freed a little space, and yet everything stayed in the cache.
The layers of the `essai-cache:bas` image still exist, and the builder reuses
them. Delete the image first, then try again:

```bash
docker rmi essai-cache:bas >/dev/null
docker builder prune -f | tail -1
docker build --progress=plain -t essai-cache:bas -f Dockerfile.bas --build-arg ETIQUETTE=b . 2>&1 | etapes
```

```text
Total:	1.409MB
[2/3] RUN apk add --no-cache jq >/dev/null && jq --version
[3/3] RUN echo "etiquette=b" > /etiquette
```

This time, both steps run again. `docker builder prune` only removes the
cache that no image uses: to really start from scratch, delete the images,
or build with `--no-cache`.

## 🧹 Clean-up

Delete the scratch images and directory. The last command counts the
`essai-*` images left:

```bash
cd ~
docker rmi essai-cache:haut essai-cache:bas essai-cache:date | grep -c Untagged
rm -rf ~/essai-cache
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
3
0
```

No scratch image left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the clean-up and then the lab preparation: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset images-ordre-des-couches
dsoxlab check images-ordre-des-couches
```

```text
╭─ Result: images-ordre-des-couches ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
untouched.

## 🎯 The challenge

Your turn, on your own this time: reorder the Dockerfile of an application
so that a code change no longer runs the installation again, while a
dependency change still does.

```bash
dsoxlab run images-ordre-des-couches
dsoxlab challenge images-ordre-des-couches
```
