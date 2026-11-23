# Run an image without root

The lesson shows that `USER` changes the identity without granting any
right, how to give a directory to the right uid, what `COPY --chown` does,
and why to declare a numeric uid. This course has you measure the cost of a
misplaced `RUN chown`, see the difference between a named volume and a host
directory mounted into the container, write into that directory under your
own uid, and enter a non-root container as root to diagnose it.

You work in `~/essai-droits`, with `essai-droits:*` images and the scratch
uid `30100`. The challenge uses another application and another uid: you
will do it on your own, at the end.

Related page: [User and permissions in an image](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/utilisateur-et-permissions/) (in French).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-non-root
```

You are now connected to `docker.lab`, a Debian 13 machine where the Docker
engine runs. Create the scratch directory and store the course's base image
in a variable. **Keep the same terminal until the clean-up**: the variable
only exists in it.

```bash
mkdir -p ~/essai-droits && cd ~/essai-droits
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
```

The outputs in this course were captured on this machine on 23 November
2026, with Docker Engine 29.9.2.

## 📏 Exercise 1: the cost of a `RUN chown`

The lesson says that `COPY --chown` saves a layer. Measure what that layer
weighs. Create a 10 MB file, then build two images that give it to uid
`30100`: one with a `RUN chown` after the `COPY`, the other with
`COPY --chown`.

```bash
head -c 10000000 /dev/urandom > donnees.bin
printf 'FROM %s\nCOPY donnees.bin /srv/donnees.bin\nRUN chown 30100:30100 /srv/donnees.bin\n' "$ALPINE" > Dockerfile.run
printf 'FROM %s\nCOPY --chown=30100:30100 donnees.bin /srv/donnees.bin\n' "$ALPINE" > Dockerfile.copy
docker build -q -t essai-droits:run -f Dockerfile.run .
docker build -q -t essai-droits:copy -f Dockerfile.copy .
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-droits:run | head -2 | cut -c1-60
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-droits:copy | head -1 | cut -c1-60
docker image ls --format '{{.Repository}}:{{.Tag}} {{.Size}}' | grep '^essai-droits'
```

```text
sha256:5966fe639b6fdeafad9523ccb581fc65497c6b6b150aecdba01fc95473b3f228
sha256:8ffd04df14162c70dd34f88abb267d33fc024fdaf43726e9f90b2086786b317c
10MB	RUN /bin/sh -c chown 30100:30100 /srv/donnee…
10MB	COPY donnees.bin /srv/donnees.bin # buildkit
10MB	COPY --chown=30100:30100 donnees.bin /srv/do…
essai-droits:copy 33MB
essai-droits:run 53MB
```

`RUN chown` does not change the file in place: it writes a new copy of it in
a new layer. The same 10 MB file is therefore stored twice, and the image
weighs 20 MB more. `COPY --chown` sets the owner at copy time, in a single
layer.

## 📂 Exercise 2: named volume or host directory

Build a non-root image that writes into `/srv/carnet`, a directory given to
uid `30100`. Run it first on a named volume, then on a directory of your home
mounted at the same place:

```bash
cat > Dockerfile.nonroot <<EOF
FROM $ALPINE
RUN mkdir -p /srv/carnet && chown 30100:30100 /srv/carnet
USER 30100:30100
CMD ["sh", "-c", "date > /srv/carnet/derniere && echo ecrit"]
EOF
docker build -q -t essai-droits:nonroot -f Dockerfile.nonroot .
docker volume create essai-carnet >/dev/null
docker run --rm -v essai-carnet:/srv/carnet essai-droits:nonroot
docker run --rm -v essai-carnet:/srv/carnet --entrypoint stat essai-droits:nonroot -c '%u:%g %n' /srv/carnet
mkdir -p ~/essai-droits/hote
docker run --rm -v ~/essai-droits/hote:/srv/carnet essai-droits:nonroot; echo "code=$?"
stat -c '%u:%g %n' ~/essai-droits/hote
```

```text
sha256:9f90851f878c1fd9ff25cc9d1fd952dc08b7e78003fdcbe62e262c1bfd20e666
ecrit
30100:30100 /srv/carnet
sh: can't create /srv/carnet/derniere: Permission denied
code=1
1001:1001 /home/ansible/essai-droits/hote
```

The named volume, empty when created, received the owner of the image's
directory (`30100:30100`): Docker copies that directory into the volume the
first time. The write succeeds. The host directory, on the other hand, is
mounted **as is**: it belongs to your account (uid 1001 here), and the
container's uid `30100` is not allowed to write into it. The `chown` of the
Dockerfile does not apply to a host directory.

## ✍️ Exercise 3: write into the host directory under your uid

To write into a host directory, the process needs a uid that is allowed to.
Run the same image under your own uid, with `--user`:

```bash
docker run --rm --user "$(id -u):$(id -g)" -v ~/essai-droits/hote:/srv/carnet essai-droits:nonroot; echo "code=$?"
ls -ln ~/essai-droits/hote | tail -1 | awk '{print $3":"$4, $9}'
```

```text
ecrit
code=0
1001:1001 derniere
```

The write succeeds, and the file created belongs to you on the host: you can
read and delete it without `sudo`. This is the usual answer for a tool that
writes into your working directory. It is not the answer for a service
image: it must write without being given an option, as in exercise 2.

## 🩺 Exercise 4: enter a non-root container as root

A non-root container cannot change anything outside what it owns, even for a
diagnosis. Run the image in the background, then compare an ordinary command
with a command run with `docker exec -u 0`:

```bash
docker run -d --name essai-veille essai-droits:nonroot sleep 300 >/dev/null
docker exec essai-veille id
docker exec essai-veille sh -c 'touch /etc/essai'; echo "code=$?"
docker exec -u 0 essai-veille id
docker exec -u 0 essai-veille sh -c 'touch /etc/essai && echo ecrit-en-root'
```

```text
uid=30100 gid=30100 groups=30100
touch: /etc/essai: Permission denied
code=1
uid=0(root) gid=0(root) groups=0(root),1(bin),2(daemon),3(sys),4(adm),6(disk),10(wheel),11(floppy),20(dialout),26(tape),27(video)
ecrit-en-root
```

`docker exec` takes the image's uid, `30100`, and cannot write into `/etc`.
With `-u 0`, the same command runs as root, in the same container. This is
useful for diagnosis, and it is also why access to the Docker engine is
worth root access: the image's `USER` does not protect against an
administrator of the engine.

## 🧹 Clean-up

Delete the container, the images, the volume and the scratch directory. The
last two commands count the `essai-*` images and volumes left:

```bash
cd ~
docker rm -f essai-veille >/dev/null
docker rmi essai-droits:run essai-droits:copy essai-droits:nonroot | grep -c Untagged
docker volume rm essai-carnet
rm -rf ~/essai-droits
docker images --format '{{.Repository}}' | grep -c '^essai-'; docker volume ls -q | grep -c '^essai-'
```

```text
3
essai-carnet
0
0
```

Nothing left from this course. Then leave the machine and reset the lab.
`dsoxlab reset` replays the clean-up and then the lab preparation: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset images-non-root
dsoxlab check images-non-root
```

```text
╭───── Result: images-non-root ─────╮
│  0 / 100 pts                      │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests  │
╰───────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
untouched.

## 🎯 The challenge

Your turn, on your own this time: run an application under a non-zero uid
declared by the image, without it losing the right to write its log, and
without opening its directory to everyone.

```bash
dsoxlab run images-non-root
dsoxlab challenge images-non-root
```
