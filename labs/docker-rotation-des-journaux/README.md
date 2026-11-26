# Rotate one container log

The lesson sets the rotation and measures the files. This course looks at what
remains in a bounded log: what can still be read, refused options, another
driver, compression, and a line that is too long.

You work in `~/essai-journal`, on `essai-*` containers. The challenge uses
`dsoxlab-log-rotation`: do not touch it during the course.

Related page: [Rotate Docker logs and reclaim disk space](https://www.stephane-robert.info/en/docs/docker/rotate-docker-logs-and-reclaim-disk-space/).

## 🔧 Before you start

Start the lab:

```bash
dsoxlab run docker-rotation-des-journaux
```

You are connected to `docker.lab`, where the engine runs. The `bavard` function
starts a container that writes 4,000 lines, `fichiers` lists its logs. **Keep
the same terminal until the cleanup**: the variables only exist in it.

```bash
mkdir -p ~/essai-journal && cd ~/essai-journal
export IMAGE=alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a
docker pull -q "$IMAGE" > /dev/null
docker version --format '{{.Server.Version}}'
bavard() { docker run -d --init --name "essai-$1" "${@:2}" "$IMAGE" sh -c 'for i in $(seq 1 4000); do echo "ligne $i"; done; sleep 600' > /dev/null; sleep 2; }
fichiers() { sudo sh -c "ls -l $(dirname "$(docker inspect "essai-$1" --format '{{.LogPath}}')")" | awk '/json.log/{print $5, $9}' | sed 's/[0-9a-f]\{64\}/ID/'; }
```

```text
29.9.2
```

The outputs of this course come from a Docker 29.9.2 on Debian 13, on 25
November 2026. Addresses and identifiers will differ on your side.

## 📏 Exercise 1: what can still be read

Bound the log, then count the lines and bytes that remain:

```bash
bavard borne --log-opt max-size=20k --log-opt max-file=2
docker logs essai-borne | wc -l
docker logs essai-borne | sed -n '1p;$p'
fichiers borne
```

```text
267
ligne 3734
ligne 4000
1537 ID-json.log
20062 ID-json.log.1
```

The current file has just started again almost empty, the other one is full:
depending on the moment, between one and two files of lines remain. Plan the
size on the shortest case.

## 🚫 Exercise 2: refused options

Get it wrong in four ways, one of which Docker accepts:

```bash
docker run --rm --log-opt max-siz=10k "$IMAGE" true 2>&1 | grep -o "unknown log opt 'max-siz'"
docker run --rm --log-opt max-size=10x "$IMAGE" true 2>&1 | grep -o "invalid suffix.*"
docker run --rm --log-opt max-size=0 "$IMAGE" true 2>&1 | grep -o "max-size must be.*"
docker run --rm --log-opt max-file=2 "$IMAGE" echo accepte
docker update --log-opt max-size=1k essai-borne 2>&1 | grep -o 'unknown flag: --log-opt'
```

```text
unknown log opt 'max-siz'
invalid suffix: 'x'
max-size must be a positive number
accepte
unknown flag: --log-opt
```

`max-file` without `max-size` is accepted and bounds nothing: no file ever
reaches its size. And a log cannot be adjusted afterwards: the container must
be recreated.

## 📦 Exercise 3: another driver

Keep the same bounds with the `local` driver:

```bash
bavard local --log-driver local --log-opt max-size=20k --log-opt max-file=2
docker logs essai-local | wc -l
docker inspect essai-local --format '[{{.LogPath}}]'
```

```text
809
[]
```

The same budget keeps more lines, because the format is more compact. `LogPath`
is empty: a tool that reads the JSON files will find nothing any more. `docker
logs` keeps working.

## 🗜️ Exercise 4: compression

Compress the rotated files, and count what remains readable:

```bash
bavard compresse --log-opt max-size=20k --log-opt max-file=5 --log-opt compress=true
fichiers compresse | grep -c gz
docker logs essai-compresse | wc -l
docker restart --timeout 1 essai-compresse > /dev/null; sleep 2
docker logs --tail 1 essai-compresse
```

```text
4
1011
ligne 4000
```

`docker logs` reads the compressed files back without asking for anything. A
restart does not empty the log: it goes on in the same files.

## 🧵 Exercise 5: a line that is too long

Write a single line of 60,000 characters, and count the records:

```bash
docker run -d --init --name essai-longue "$IMAGE" sh -c 'head -c 60000 /dev/zero | tr "\0" a; echo; sleep 600' > /dev/null; sleep 1
docker logs essai-longue | wc -l
sudo cat "$(docker inspect essai-longue --format '{{.LogPath}}')" | wc -l
```

```text
1
4
```

Docker splits a long line into 16 KiB records. `docker logs` puts it back
together, but a tool that reads the file sees four pieces, the first of which
are not complete lines: a long JSON message becomes unreadable there.

## 🧹 Cleanup

```bash
cd ~
docker rm -f essai-borne essai-local essai-compresse essai-longue > /dev/null
rm -rf ~/essai-journal
docker ps -a --format '{{.Names}}' | grep -c '^essai-'
```

```text
0
```

Then leave the machine and reset the lab. `dsoxlab reset` replays the cleanup
then the setup of the lab. It asks you to confirm: answer `y`.

```bash
exit
dsoxlab reset docker-rotation-des-journaux
dsoxlab check docker-rotation-des-journaux
```

```text
╭─ Result: docker-rotation-des-journaux ─╮
│  0 / 100 pts                           │
│  ░░░░░░░░░░░░░░░░░░░░  0/3 tests       │
╰────────────────────────────────────────╯
```

0 out of 3: that is the expected result. The challenge is ready.

## 🎯 The challenge

Your turn, on your own this time: one chatty service, only one, to contain
without touching the others.

```bash
dsoxlab run docker-rotation-des-journaux
dsoxlab challenge docker-rotation-des-journaux
```
