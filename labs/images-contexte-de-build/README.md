# Master the build context

The lesson explains that `docker build` only sees its context, how to widen
it with `-f`, and how to keep a sensitive file out of it. This course has you
check what the builder really receives, write exclusions with an exception,
extract from an image a file that was deleted, and build with no context at
all.

You work in scratch directories of your home directory, with `essai-*`
images. The challenge uses another repository and another Dockerfile: you
will do it on your own, at the end.

Related page: [Write a Dockerfile](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/ecrire-dockerfile/) (in French).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-contexte-de-build
```

You are now connected to `docker.lab`, a Debian 13 machine where the Docker
engine runs. The outputs in this course were captured on this machine on
23 November 2026, with Docker Engine 29.9.2.

## 📦 Exercise 1: see what the builder receives

The context is what `docker build` sends to the builder. To see it, write a
Dockerfile that copies the whole context and then lists what it received.
The `--progress=plain` option shows the output of `RUN` commands.

```bash
mkdir -p ~/essai-contexte/journaux ~/essai-contexte/brouillons && cd ~/essai-contexte
echo rapport > rapport.txt
echo a > journaux/lundi.log
echo b > journaux/garder.log
echo c > brouillons/idee.txt
cat > Dockerfile <<'EOF'
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
COPY . /contexte
RUN find /contexte -type f | sort
EOF
docker build --no-cache --progress=plain -t essai-contexte:1 . 2>&1 | grep -E '^#[0-9]+ [0-9.]+ /contexte|transferring context'
```

```text
#3 transferring context: 2B done
#5 transferring context: 436B done
#7 0.125 /contexte/Dockerfile
#7 0.125 /contexte/brouillons/idee.txt
#7 0.125 /contexte/journaux/garder.log
#7 0.125 /contexte/journaux/lundi.log
#7 0.125 /contexte/rapport.txt
```

The first `transferring context` line is about the Dockerfile, the second
about the context: a few hundred bytes. The five files of the directory
arrived, Dockerfile included: a `COPY .` takes everything the context holds.

## 🚫 Exercise 2: exclude by patterns, with an exception

A `.dockerignore` accepts patterns. Leave out the drafts directory and all
`.log` files, except `journaux/garder.log`, which you bring back with a `!`.
Then build again:

```bash
cat > .dockerignore <<'EOF'
brouillons/
**/*.log
!journaux/garder.log
EOF
docker build --no-cache --progress=plain -t essai-contexte:2 . 2>&1 | grep -E '^#[0-9]+ [0-9.]+ /contexte'
```

```text
#7 0.134 /contexte/.dockerignore
#7 0.134 /contexte/Dockerfile
#7 0.134 /contexte/journaux/garder.log
#7 0.134 /contexte/rapport.txt
```

`brouillons/` and `lundi.log` are no longer sent. `garder.log` comes back
thanks to the `!` line, which must come **after** the pattern it corrects:
lines are read in order, and the last one that matches wins. The
`.dockerignore` itself enters the image, because nothing excludes it.

## 🔍 Exercise 3: a deleted file stays in the image

The lesson says that adding a `RUN rm` does not remove a file from the image.
Check it yourself: copy a private note, delete it in the next instruction,
then look for its content in the image layers.

```bash
mkdir -p ~/essai-couche && cd ~/essai-couche
echo MotDePasse-Essai-42 > note-privee.txt
cat > Dockerfile <<'EOF'
FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
COPY note-privee.txt /tmp/
RUN rm /tmp/note-privee.txt
EOF
docker build -q -t essai-couche:1 .
docker run --rm essai-couche:1 ls -A /tmp | wc -l
docker history --format '{{.CreatedBy}}' essai-couche:1 | head -3
```

```text
sha256:29f1eb12fb14943246c233acf5ab71ab73ef926810d823403be1a3f7a38412a5
0
RUN /bin/sh -c rm /tmp/note-privee.txt # bui…
COPY note-privee.txt /tmp/ # buildkit
CMD ["/bin/sh"]
```

In a container started from the image, `/tmp` is empty: 0 files. But
`docker history` shows that the `COPY` layer still exists, under the `RUN rm`
layer. Now export the image with `docker save`, then look for the password in
each of its layers:

```bash
mkdir extrait && docker save essai-couche:1 | tar -x -C extrait
for c in $(find extrait/blobs -type f); do tar -xOf "$c" 2>/dev/null | grep -a -q MotDePasse-Essai-42 && echo "trouvé dans la couche $(basename "$c" | cut -c1-12)"; done
```

```text
trouvé dans la couche 4b0310bcf1a4
```

The password can be read in one of the image layers. Anyone who gets the
image finds it the same way. The `RUN rm` only added a layer that hides the
file. Only an exclusion from the context would have kept it out.

## 🧱 Exercise 4: build with no context at all

`docker build -` reads the Dockerfile from standard input, and sends **no**
context. Build two Dockerfiles this way: one only does a `RUN`, the other a
`COPY`.

```bash
mkdir -p ~/essai-sans && cd ~/essai-sans
printf 'FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a\nRUN echo construit sans contexte\n' > Dockerfile.run
printf 'FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a\nCOPY rapport.txt /\n' > Dockerfile.copy
docker build -q -t essai-sans:run - < Dockerfile.run
docker build -t essai-sans:copy - < Dockerfile.copy 2>&1 | tail -1
```

```text
sha256:9b3605b0165e869f05b025e042ed49d6dc0ed81550e51616b077818d4a63c4e1
ERROR: failed to build: failed to solve: failed to compute cache key: failed to calculate checksum of ref rkzv83qyclf9yx7nyebxnoute::h2ug2pc3u64fwu6cyb4md7ca9: "/rapport.txt": not found
```

The first one builds: a `RUN` needs no file. The second one fails with
`not found`, the same message as in the lesson, although there is no typo:
without a context, `COPY` has nowhere to look. In front of this message,
always ask yourself first what the builder received.

## 🧹 Clean-up

Delete the scratch images and directories. The last command counts the
`essai-*` images left:

```bash
cd ~
docker rmi essai-contexte:1 essai-contexte:2 essai-couche:1 essai-sans:run | grep -c Untagged
rm -rf ~/essai-contexte ~/essai-couche ~/essai-sans
docker images --format '{{.Repository}}' | grep -c '^essai-'
```

```text
4
0
```

No scratch image left. Then leave the machine and reset the lab.
`dsoxlab reset` replays the clean-up and then the lab preparation: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset images-contexte-de-build
dsoxlab check images-contexte-de-build
```

```text
╭─ Result: images-contexte-de-build ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests   │
╰────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
untouched.

## 🎯 The challenge

Your turn, on your own this time: build an application whose Dockerfile
needs a shared file outside its directory, without letting a secret that
sits next to it into the image.

```bash
dsoxlab run images-contexte-de-build
dsoxlab challenge images-contexte-de-build
```
