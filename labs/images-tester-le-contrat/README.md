# Write the tests that turn a broken image away

The lesson writes a complete test script. This course shows five reasons why a
test written in good faith accepts what it should refuse: a failure swallowed
by the shell, a 500 response taken for a success, a message looked for in the
wrong place, an endless wait, and debris left behind.

You work in `~/essai-tests`, on `essai-*` containers. The challenge uses
`/opt/dsoxlab-images-tester-le-contrat`: do not touch it during the course.

Related page: [Test the contract of an image](https://www.stephane-robert.info/en/docs/docker/test-an-image-contract/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run images-tester-le-contrat
```

You are connected to `docker.lab`, where the engine runs. **Keep the same
terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-tests && cd ~/essai-tests
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 🫥 Exercise 1: a failure swallowed by the shell

Three scripts start with `set -e`. Guess which ones stop:

```bash
printf 'set -e\nverifier() { false; echo "arrive ici"; }\nif verifier; then echo accepte; fi\n' > a.sh
printf 'set -e\nverifier() { local v=$(false); echo "arrive ici"; }\nverifier\n' > b.sh
printf 'set -e\nv=$(false)\necho "arrive ici"\n' > c.sh
for f in a b c; do bash $f.sh; echo "$f: $?"; done
```

```text
arrive ici
accepte
a: 0
arrive ici
b: 0
c: 1
```

Only the last one stops. `set -e` is suspended in a function called by an `if`,
an `&&` or an `||`, and `local` replaces the command's code with its own. Write
the refusal yourself: `command || { echo "REFUSED"; exit 1; }`.

## 🌐 Exercise 2: a 500 response taken for a success

A service always answers 500. Query it in two ways:

```bash
docker run -d --init --name essai-web -p 127.0.0.1::8080 "$IMAGE" nc -lk -p 8080 -e printf 'HTTP/1.1 500 Panne\r\nContent-Length: 3\r\nConnection: close\r\n\r\nko\n' > /dev/null
sleep 1
PORT=$(docker port essai-web 8080/tcp | cut -d: -f2)
curl -s "http://127.0.0.1:$PORT/"; echo "sans -f: $?"
curl -fsS "http://127.0.0.1:$PORT/"; echo "avec -f: $?"
docker rm -f essai-web > /dev/null
```

```text
ko
sans -f: 0
curl: (22) The requested URL returned error: 500
avec -f: 22
```

Without `-f`, `curl` returns 0 as soon as a response arrives, whatever its
code. A test needs `-f`, and often a comparison of the content too: an empty
200 is not a working service.

## 🔍 Exercise 3: a message looked for in the wrong place

A program refuses to start and says so. Look for its message:

```bash
docker run --name essai-dit "$IMAGE" sh -c 'echo "VARIABLE manquante" >&2; exit 1' 2> /dev/null; echo "code: $?"
docker logs essai-dit 2> /dev/null | grep -c manquante
docker logs essai-dit 2>&1 | grep -c manquante
docker rm essai-dit > /dev/null
docker run --rm essai-absente:1 true > /dev/null 2>&1; echo "image absente: $?"
```

```text
code: 1
0
1
image absente: 125
```

The message is on the error output: without `2>&1`, `grep` does not see it and
the test concludes wrongly. The last line shows another trap: 125 comes from
Docker, not from the image. A test content with any non-zero code would accept
that failure as a refusal.

## ⏱️ Exercise 4: an endless wait

Wait for the end of two containers, one of which does not end:

```bash
docker run -d --init --name essai-court "$IMAGE" sh -c 'sleep 1; exit 4' > /dev/null
timeout 5 docker wait essai-court; echo "timeout: $?"
docker run -d --init --name essai-long "$IMAGE" sleep 600 > /dev/null
timeout 2 docker wait essai-long; echo "timeout: $?"
docker rm -f essai-court essai-long > /dev/null
```

```text
4
timeout: 0
timeout: 124
```

`docker wait` prints the container's code, and `timeout` returns 124 when it
had to cut. These are two pieces of information: "it stopped with 4" and "it
did not stop". Read both.

## 🧹 Exercise 5: debris left behind

A script fails halfway, without then with a cleanup on exit. Also look at an
anonymous volume:

```bash
printf 'set -e\ndocker run -d --init --name essai-debris "$IMAGE" sleep 600 > /dev/null\nfalse\ndocker rm -f essai-debris\n' > sans.sh
printf 'set -e\ntrap "docker rm -f essai-propre > /dev/null" EXIT\ndocker run -d --init --name essai-propre "$IMAGE" sleep 600 > /dev/null\nfalse\n' > avec.sh
bash sans.sh; echo "sans: $?, reste $(docker ps -q --filter name=essai-debris | wc -l)"
bash avec.sh; echo "avec: $?, reste $(docker ps -q --filter name=essai-propre | wc -l)"
docker rm -f essai-debris > /dev/null
printf 'FROM %s\nVOLUME /donnees\n' "$IMAGE" > Dockerfile
docker build -q -t essai-tests:vol . > /dev/null
AVANT=$(docker volume ls -q | wc -l)
docker run -d --init --name essai-vol essai-tests:vol sleep 600 > /dev/null
VOLUME=$(docker inspect essai-vol --format '{{(index .Mounts 0).Name}}')
docker rm -f essai-vol > /dev/null; echo "volumes en plus: $(( $(docker volume ls -q | wc -l) - AVANT ))"
docker volume rm "$VOLUME" > /dev/null
```

```text
sans: 1, reste 1
avec: 1, reste 0
volumes en plus: 1
```

The `trap ... EXIT` runs on any exit, including after a failure, and keeps the
code. An image that declares `VOLUME` creates an anonymous volume that `docker
rm -f` leaves behind: you need `docker rm -f -v`.

## 🧹 Cleanup

```bash
cd ~
docker images 'essai-tests' --format '{{.Repository}}:{{.Tag}}' | xargs -r docker rmi -f > /dev/null
rm -r ~/essai-tests
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
dsoxlab reset images-tester-le-contrat
dsoxlab check images-tester-le-contrat
```

```text
╭─ Result: images-tester-le-contrat ─╮
│  0 / 100 pts                       │
│  ░░░░░░░░░░░░░░░░░░░░  0/6 tests   │
╰────────────────────────────────────╯
```

0 out of 6: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: one good image, bad ones you have not seen,
and a script that tells them apart.

```bash
dsoxlab run images-tester-le-contrat
dsoxlab challenge images-tester-le-contrat
```
