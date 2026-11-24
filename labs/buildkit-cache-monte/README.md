# Keep a cache between two builds with a mount

The lesson shows that a `RUN --mount=type=cache` gives a command a directory
that survives from one build to the next without entering the image, and
that it avoids downloading a dependency again when the lock file changes.
This course has you watch that directory grow from build to build, share it
between two Dockerfiles by its identifier, and measure what empties it.

You work in `~/essai-montage`, with `essai-montage:*` images and caches named
`essai-*`. The challenge uses another tool, another dependency repository and
a dedicated builder: you will do it on your own, at the end.

Related page: [Dockerfile best practices](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/dockerfile-bonnes-pratiques/) (in French).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run buildkit-cache-monte
```

You are now connected to `docker.lab`, a Debian 13 machine where the Docker
engine runs. Create the scratch directory and store the base image in a
variable. **Keep the same terminal until the clean-up**: the variable only
exists in it.

```bash
mkdir -p ~/essai-montage && cd ~/essai-montage
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
```

The outputs in this course were captured on this machine on 23 November
2026, with Docker Engine 29.9.2 and the default builder.

## 📈 Exercise 1: a directory that survives from one build to the next

Write a Dockerfile whose `RUN` step appends a line to a file of the mounted
cache, then counts its lines. The `ARG TOUR` changes on each build, which
forces the step to run again. Build three times, then check whether the
cache is in the image:

```bash
cat > Dockerfile.passages <<EOF
FROM $ALPINE
ARG TOUR=0
RUN --mount=type=cache,id=essai-passages,target=/cache \
    echo "tour \$TOUR" >> /cache/passages && echo "passages=\$(wc -l < /cache/passages)" > /resultat
EOF
for tour in 1 2 3; do
  docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=$tour . >/dev/null
  docker run --rm essai-montage:passages cat /resultat
done
docker run --rm essai-montage:passages sh -c 'ls -A /cache 2>/dev/null | wc -l'
```

```text
passages=1
passages=2
passages=3
0
```

The count goes from 1 to 3: on each build, the step finds the lines left by
the previous one. And the image holds no file under `/cache`: the directory
is mounted for the duration of the `RUN`, then removed. Only what the step
writes elsewhere (here `/resultat`) enters the layer.

## 🔗 Exercise 2: share a cache by its identifier

A mounted cache is designated by its `id`, not by its path. Two different
Dockerfiles, mounting it at two different places, therefore see the same
content. The first one drops a file into it, the second one reads it:

```bash
cat > Dockerfile.ecrit <<EOF
FROM $ALPINE
RUN --mount=type=cache,id=essai-partage,target=/depot \
    echo "paquet-1.0" > /depot/paquet.txt
EOF
cat > Dockerfile.lit <<EOF
FROM $ALPINE
RUN --mount=type=cache,id=essai-partage,target=/ailleurs \
    cat /ailleurs/paquet.txt > /trouve
EOF
docker build -q -t essai-montage:ecrit -f Dockerfile.ecrit . >/dev/null
docker build -q -t essai-montage:lit -f Dockerfile.lit . >/dev/null
docker run --rm essai-montage:lit cat /trouve
```

```text
paquet-1.0
```

The second build read, under `/ailleurs`, the file written by the first one
under `/depot`. Without an `id`, the cache uses the `target` path as its
identifier: two projects that both mount `/root/.cache/pip` then share their
cache without having decided to.

## 🧹 Exercise 3: what empties the mounted cache

Take the Dockerfile of exercise 1 again. Build a fourth round, empty the
build cache, build a fifth round, then a sixth one with `--no-cache`:

```bash
docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=4 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
docker builder prune -f | tail -1
docker build -q -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=5 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
docker build -q --no-cache -t essai-montage:passages -f Dockerfile.passages --build-arg TOUR=6 . >/dev/null
docker run --rm essai-montage:passages cat /resultat
```

```text
passages=4
Total:	82.49kB
passages=1
passages=1
```

The fourth round finds the three previous lines. After
`docker builder prune`, the count starts again at 1: the mounted cache is
part of the build cache, and the clean-up deletes it. With `--no-cache`, it
also starts again at 1, although nothing was cleaned: the option ignores the
mounted cache along with the layers. A Dockerfile must therefore work with
an empty mounted cache.

## 🚫 Exercise 4: a refused cache

A non-root image often builds under its own uid. Give it a mounted cache, first
without any setting, then with the `uid` option:

```bash
cat > Dockerfile.refus <<EOF
FROM $ALPINE
USER 30100
RUN --mount=type=cache,id=essai-droits,target=/reserve echo paquet > /reserve/paquet
EOF
docker build -t essai-montage:droits -f Dockerfile.refus . 2>&1 | grep -oE "can't create.*denied|exit code: [0-9]+" | sort -u
sed 's|target=/reserve|target=/reserve,uid=30100|' Dockerfile.refus > Dockerfile.droits
docker build -q -t essai-montage:droits -f Dockerfile.droits . > /dev/null; echo "code: $?"
```

```text
can't create /reserve/paquet: Permission denied
exit code: 1
code: 0
```

The mounted directory belongs to root: the step fails on a right, although the
Dockerfile holds no syntax error. The `uid` option gives the cache to the build
user. Do not answer this refusal with `USER root`: the step would produce files
the application could no longer change.

## 🧹 Clean-up

Delete the scratch images and directory, then the mounted caches the course
created (`--filter type=exec.cachemount` targets only them). The last command
counts the `essai-*` images left:

```bash
cd ~
docker rmi essai-montage:passages essai-montage:ecrit essai-montage:lit essai-montage:droits | grep -c Untagged
rm -rf ~/essai-montage
docker builder prune -f --filter type=exec.cachemount | tail -1
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
4
Total:	12.29kB
0
```

Nothing left from this course. Then leave the machine and reset the lab.
`dsoxlab reset` replays the clean-up and then the lab preparation: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset buildkit-cache-monte
dsoxlab check buildkit-cache-monte
```

```text
╭── Result: buildkit-cache-monte ───╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests  │
╰───────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is waiting for you,
untouched.

## 🎯 The challenge

Your turn, on your own this time: make a step that runs again on every
source change reuse a dependency, without the cache entering the image.

```bash
dsoxlab run buildkit-cache-monte
dsoxlab challenge buildkit-cache-monte
```
