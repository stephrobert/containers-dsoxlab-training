# Migrate an image to a lighter base

The lesson shows what a base image provides, why changing the `FROM` line
makes a script or a binary fail, and how to choose between rewriting and
reinstalling. This course has you record the contract of a third base,
diagnose a shebang that goes through `env`, track down a bash construct that
fails silently, fix Alpine's time zones, and prove from the layers that an
image really changed its base.

You work in `~/essai-socle`, with `essai-socle:*` images. The challenge uses
another application and another script: you will do it on your own, at the
end.

Related page: [Choose a base image](https://www.stephane-robert.info/docs/conteneurs/images-conteneurs/choisir-une-image-de-base/) (in French).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-migrer-vers-alpine
```

You are now connected to `docker.lab`, a Debian 13 machine where the Docker
engine runs. Create the scratch directory, and store in two variables the
base images of this course, pinned by their digest. **Keep the same terminal
until the clean-up**: the variables only exist in it.

```bash
mkdir -p ~/essai-socle && cd ~/essai-socle
ALPINE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
BUSYBOX=busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
```

The outputs in this course were captured on this machine on 23 November
2026, with Docker Engine 29.9.2.

## 🔎 Exercise 1: record the contract of a third base

The lesson compares Alpine and Debian. Record the same contract on
`busybox`, an even smaller base: its libc, its package manager, its root
certificates and its number of accounts.

```bash
for image in "$ALPINE" "$BUSYBOX"; do
  echo "== ${image%%@*}"
  docker run --rm "$image" sh -c 'ls /lib/libc.musl-x86_64.so.1 >/dev/null 2>&1 && echo musl || { ls /lib/libc.so.6 >/dev/null 2>&1 && echo glibc || echo "libc ?"; }; command -v apk || echo "pas de apk"; ls /etc/ssl/certs/ca-certificates.crt 2>/dev/null || echo "certificats absents"; wc -l < /etc/passwd'
done
```

```text
== alpine:3.24.3
musl
/sbin/apk
/etc/ssl/certs/ca-certificates.crt
17
== busybox:1.37.0
Unable to find image 'busybox:1.37.0@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec' locally
docker.io/library/busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec: Pulling from library/busybox
68fe9bff2ad4: Pulling fs layer
68fe9bff2ad4: Download complete
68fe9bff2ad4: Pull complete
9177639ff916: Download complete
Digest: sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
Status: Downloaded newer image for busybox@sha256:a7dbc319b1438115a207e11930dc4bb3e643dcb3ec0bdd694bb36cd8fad289ec
glibc
pas de apk
certificats absents
9
```

The default `busybox` image is built on **glibc**, not on musl like Alpine.
It has neither a package manager nor root certificates, and only 9 accounts.
Nothing can be installed in it: everything an application needs there must
be copied at build time. The `Pulling` lines at the start come from the first
download of the image.

## 🐍 Exercise 2: a shebang that goes through env

Many scripts start with `#!/usr/bin/env python3`, to find the interpreter
wherever it is. Ship such a script on Alpine, then run it:

```bash
printf '#!/usr/bin/env python3\nprint("bonjour")\n' > salut && chmod +x salut
printf 'FROM %s\nCOPY salut /usr/local/bin/salut\nCMD ["/usr/local/bin/salut"]\n' "$ALPINE" > Dockerfile.env
docker build -q -t essai-socle:env -f Dockerfile.env .
docker run --rm essai-socle:env; echo "code=$?"
docker run --rm --entrypoint sh essai-socle:env -c 'head -1 /usr/local/bin/salut; command -v python3 || echo "python3 absent"'
```

```text
sha256:8bba4c2f7a7bed635dfd803dac53ccfc6fbd90533d7655a3385d0f5efb7890b4
env: can't execute 'python3': No such file or directory
code=127
#!/usr/bin/env python3
python3 absent
```

The message is no longer the lesson's. `env` exists on Alpine: it is the one
that starts, then fails while finally naming the real missing piece,
`python3`. With a direct shebang (`#!/usr/bin/python3`), you would have got
the misleading `no such file or directory` on the script. In both cases,
`head -1` gives the answer.

## 🔁 Exercise 3: a bash construct that fails silently

A script declared `#!/bin/sh` can contain bash constructs. Write a script that
counts from 1 to 3 with `{1..3}` and tests a variable with `[[ ]]`, then run
it on Alpine:

```bash
cat > compter <<'EOF'
#!/bin/sh
for i in {1..3}; do echo "tour $i"; done
if [[ -n "$HOME" ]]; then echo "maison=$HOME"; fi
EOF
chmod +x compter
printf 'FROM %s\nCOPY compter /usr/local/bin/compter\nCMD ["/usr/local/bin/compter"]\n' "$ALPINE" > Dockerfile.sh
docker build -q -t essai-socle:sh -f Dockerfile.sh .
docker run --rm essai-socle:sh; echo "code=$?"
```

```text
sha256:62493ff03d00529c3f1580f995260239894dc4c5805f758055e3c1c6109fac41
tour {1..3}
maison=/root
code=0
```

No error, and the exit code is 0. Yet the loop ran only once, with `{1..3}`
taken as text: Alpine's shell does not know this bash expansion and does not
complain. `[[ ]]` worked, because the BusyBox shell accepts it. A migration is
therefore checked on the **result**, not on the absence of errors. Rewrite
the script in POSIX, then run it again:

```bash
cat > compter <<'EOF'
#!/bin/sh
for i in 1 2 3; do echo "tour $i"; done
if [ -n "$HOME" ]; then echo "maison=$HOME"; fi
EOF
docker build -q -t essai-socle:sh -f Dockerfile.sh .
docker run --rm essai-socle:sh; echo "code=$?"
```

```text
sha256:1fa164957d4f8c927512b043363bd5a9b666c457cd2656b02087f5ba57b12da4
tour 1
tour 2
tour 3
maison=/root
code=0
```

Three rounds this time. The `1 2 3` list and the `[ ]` test are understood by
every POSIX shell, and the script no longer depends on the base's shell.

## 🕒 Exercise 4: missing time zones

The lesson notes that Alpine has no time zone database. Ask an Alpine
container for the time in Paris, then add the `tzdata` package and try
again. `docker history` measures what the package adds:

```bash
docker run --rm -e TZ=Europe/Paris "$ALPINE" date +'%H:%M %Z'
printf 'FROM %s\nRUN apk add --no-cache tzdata\n' "$ALPINE" > Dockerfile.tz
docker build -q -t essai-socle:tz -f Dockerfile.tz .
docker run --rm -e TZ=Europe/Paris essai-socle:tz date +'%H:%M %Z'
docker history --format '{{.Size}}\t{{.CreatedBy}}' essai-socle:tz | head -2 | cut -c1-70
```

```text
18:27 UTC
sha256:a06000a39ad5d907377f512dca48b7d1188b71dcef3711ac471ba756a51931b5
19:27 CET
1.66MB	RUN /bin/sh -c apk add --no-cache tzdata # b…
0B	CMD ["/bin/sh"]
```

Without `tzdata`, the `TZ` variable is ignored with no message: the time
stays in UTC. With the package, it switches to Paris time (CET, one hour
ahead in November). The added layer weighs about 1.7 MB: that is the price of
this fix, to compare with the 9 MB of the base.

## 🧱 Exercise 5: prove from the layers that an image changed its base

The `essai-socle:tz` image is built on Alpine. Compare its layers with those
of the base:

```bash
docker image inspect "$ALPINE" --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep -v '^$'
echo --
docker image inspect essai-socle:tz --format '{{range .RootFS.Layers}}{{println .}}{{end}}' | grep -v '^$'
```

```text
sha256:75c137aedfb2760f88629236cb7b797630aed0c3d91d626d1d1bb694878fc2ba
--
sha256:75c137aedfb2760f88629236cb7b797630aed0c3d91d626d1d1bb694878fc2ba
sha256:3c631e868767dbe538bea1f033b4ed196580b98d76d986dc1499a34d598f1322
```

The base has a single layer, and it is the **first** layer of the image: that
is the proof that the image rests on it. The second layer is the one from
`RUN apk add`. An image built on another base would have another first
layer, even if it weighed the same.

## 🧹 Clean-up

Delete the scratch images, the downloaded `busybox` image and the directory.
The last command counts what is left:

```bash
cd ~
docker rmi essai-socle:env essai-socle:sh essai-socle:tz | grep -c Untagged
docker rmi "$BUSYBOX" >/dev/null; rm -rf ~/essai-socle
docker images --format '{{.Repository}}' | grep -c -e '^essai-' -e '^busybox$'
```

```text
3
0
```

Nothing left from this course. Then leave the machine and reset the lab.
`dsoxlab reset` replays the clean-up and then the lab preparation: you get
back exactly the starting state of the challenge. It asks you to confirm:
answer `y`.

```bash
exit
dsoxlab reset images-migrer-vers-alpine
dsoxlab check images-migrer-vers-alpine
```

```text
╭─ Result: images-migrer-vers-alpine ─╮
│  0 / 100 pts                        │
│  ░░░░░░░░░░░░░░░░░░░░  0/4 tests    │
╰─────────────────────────────────────╯
```

0 out of 4: that is the expected result. The challenge is waiting for you,
untouched.

## 🎯 The challenge

Your turn, on your own this time: move an application from a Debian base to
an Alpine base, without losing its result, and prove that it really changed
its base.

```bash
dsoxlab run images-migrer-vers-alpine
dsoxlab challenge images-migrer-vers-alpine
```
